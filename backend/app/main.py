import os
import base64
from datetime import datetime, timedelta
from typing import List
import json
import uvicorn
from contextlib import asynccontextmanager

import asyncio
import time

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import Base, engine, get_db, SessionLocal
from app.models import AlertLog, Zone
from app.schemas import DetectionPayload, AlertOut, ZoneCreate, ZoneOut, DispatchRequest, DispatchResponse
from app.fusion import fusion_engine
from app.hardware import hardware_bridge
from app.utils import cleanup_old_thumbnails
from app.auth import verify_api_key

Base.metadata.create_all(bind=engine)

THUMBNAIL_DIR = "static/thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

def seed_default_zone():
    """Ensures DB schema compatibility and seeds tactical border zones across all sectors."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN status VARCHAR DEFAULT 'PENDING'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE zones ADD COLUMN radius_meters FLOAT DEFAULT 500.0"))
            conn.commit()
        except Exception:
            pass

    default_zones = [
        {"zone_id": "ZONE_GATEWAY", "name": "Sector 01 - Gateway Alpha", "camera_id": "cam-01", "lat": 31.4385, "lng": 74.3210, "radius_meters": 500.0},
        {"zone_id": "ZONE_BRAVO", "name": "Sector 02 - Fence Bravo", "camera_id": "cam-02", "lat": 31.4398, "lng": 74.3245, "radius_meters": 500.0},
        {"zone_id": "ZONE_RIVERINE", "name": "Sector 03 - Riverine Watch", "camera_id": "cam-03", "lat": 31.4421, "lng": 74.3270, "radius_meters": 500.0},
        {"zone_id": "ZONE_A", "name": "Sector 04 - North Perimeter", "camera_id": "cam-04", "lat": 31.4392, "lng": 74.3298, "radius_meters": 500.0},
    ]

    db = SessionLocal()
    try:
        for z_data in default_zones:
            existing = db.query(Zone).filter((Zone.zone_id == z_data["zone_id"]) | (Zone.name == z_data["zone_id"])).first()
            if not existing:
                new_zone = Zone(
                    zone_id=z_data["zone_id"],
                    name=z_data["name"],
                    camera_id=z_data["camera_id"],
                    lat=z_data["lat"],
                    lng=z_data["lng"],
                    radius_meters=z_data["radius_meters"]
                )
                db.add(new_zone)
                print(f"[Database Seed] Seeded tactical border zone: {z_data['zone_id']} ({z_data['camera_id']})")
        db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_old_thumbnails()
    seed_default_zone()
    yield

app = FastAPI(
    title="Sima-Drishti Surveillance API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ai_engine", "media"))
if os.path.exists(MEDIA_DIR):
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

class VideoStreamManager:
    def __init__(self):
        self.frames = {}
        self.latest_frame: bytes = b""
        self.last_frame_time: float = 0.0
        self.active_cam: str = "cam-04"

    def set_frame(self, frame_bytes: bytes, cam_id: str = "cam-04"):
        now = time.time()
        c_id = str(cam_id).strip().lower()
        self.latest_frame = frame_bytes
        self.last_frame_time = now
        self.active_cam = c_id
        self.frames[c_id] = {"bytes": frame_bytes, "time": now}

    async def get_frame_stream(self, cam_id: str | None = None):
        target_cam = str(cam_id).strip().lower() if cam_id else None
        last_sent_time = 0.0
        try:
            while True:
                now = time.time()
                frame_data = None
                if target_cam:
                    # Strictly isolate stream to the requested camera - never leak other camera feeds
                    if target_cam in self.frames and (now - self.frames[target_cam]["time"] < 6.0):
                        frame_data = self.frames[target_cam]
                elif self.latest_frame and (now - self.last_frame_time < 6.0):
                    frame_data = {"bytes": self.latest_frame, "time": self.last_frame_time}

                if frame_data and frame_data["time"] != last_sent_time:
                    last_sent_time = frame_data["time"]
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_data["bytes"] + b"\r\n"
                    )
                await asyncio.sleep(0.035)
        except (asyncio.CancelledError, GeneratorExit):
            return

video_stream_manager = VideoStreamManager()

@app.post("/stream/frame")
async def upload_stream_frame(request: Request, cam_id: str = "cam-04"):
    """Ingests real-time JPEG frames from edge AI pipeline for any camera."""
    body = await request.body()
    if body:
        header_cam = request.headers.get("X-Camera-ID") or request.query_params.get("cam_id") or cam_id
        target_cam = str(header_cam).strip().lower()
        video_stream_manager.set_frame(body, target_cam)
        return {"status": "ok", "bytes": len(body), "cam_id": target_cam}
    return {"status": "empty"}

@app.get("/stream/video_feed")
async def stream_video_feed(cam_id: str | None = None):
    """MJPEG stream endpoint consumed by web dashboard."""
    return StreamingResponse(
        video_stream_manager.get_frame_stream(cam_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/stream/status")
def stream_status(cam_id: str | None = None):
    """Returns streaming health, active camera, and all actively broadcasting camera IDs."""
    now = time.time()
    active_cams = [cid for cid, f in video_stream_manager.frames.items() if (now - f["time"] < 5.0)]
    age = now - video_stream_manager.last_frame_time if video_stream_manager.last_frame_time > 0 else 999.0
    return {
        "is_streaming": age < 5.0,
        "active_cam": video_stream_manager.active_cam,
        "active_cams": active_cams,
        "last_frame_age_seconds": round(age, 2),
        "frame_size_bytes": len(video_stream_manager.latest_frame)
    }



@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    return {
        "status": "active",
        "service": "Sima-Drishti Backend",
        "active_ws_clients": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_alerts = db.query(AlertLog).count()
    total_zones = db.query(Zone).count()
    last_24h = datetime.utcnow() - timedelta(hours=24)
    alerts_last_24h = db.query(AlertLog).filter(AlertLog.timestamp >= last_24h).count()
    
    return {
        "total_alerts": total_alerts,
        "alerts_last_24h": alerts_last_24h,
        "active_zones": total_zones,
        "hardware_status": "fallback_mode" if hardware_bridge.serial_conn is None else "connected"
    }

@app.post("/zones", response_model=ZoneOut)
def create_zone(zone_in: ZoneCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    existing = db.query(Zone).filter(Zone.zone_id == zone_in.zone_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Zone ID already exists")
    new_zone = Zone(**zone_in.model_dump())
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    return new_zone

@app.get("/zones", response_model=List[ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    return db.query(Zone).all()

@app.get("/cameras")
def list_cameras(db: Session = Depends(get_db)):
    # Dynamically determine camera status based on recent alerts (within last 45 seconds)
    recent_threshold = datetime.utcnow() - timedelta(seconds=45)
    recent_alerts = db.query(AlertLog).filter(
        AlertLog.timestamp >= recent_threshold,
        AlertLog.status == "PENDING"
    ).all()

    alerting_cams = set()
    for a in recent_alerts:
        z = db.query(Zone).filter((Zone.zone_id == a.zone) | (Zone.name == a.zone)).first()
        if z and z.camera_id:
            alerting_cams.add(z.camera_id.lower())

    cameras_def = [
        {
            "id": "cam-01",
            "name": "CAM-01 · GATE ALPHA",
            "sector": "SEC-1",
            "sector_name": "SECTOR 1A · GATEWAY ALPHA",
            "rtsp_url": "rtsp://192.168.1.101:554/ch01/main",
            "resolution": "1080P · 30 FPS",
            "fps": 30,
            "lat": 31.4385,
            "lng": 74.3210
        },
        {
            "id": "cam-02",
            "name": "CAM-02 · FENCE BRAVO",
            "sector": "SEC-2",
            "sector_name": "SECTOR 2B · FENCE PERIMETER BRAVO",
            "rtsp_url": "rtsp://192.168.2.102:554/ch01/main",
            "resolution": "2K · 30 FPS",
            "fps": 30,
            "lat": 31.4398,
            "lng": 74.3245
        },
        {
            "id": "cam-03",
            "name": "CAM-03 · RIVERINE WATCH",
            "sector": "SEC-3",
            "sector_name": "SECTOR 3C · RIVERINE EMBANKMENT",
            "rtsp_url": "rtsp://192.168.3.103:554/ch01/main",
            "resolution": "1080P · 28 FPS",
            "fps": 28,
            "lat": 31.4421,
            "lng": 74.3270
        },
        {
            "id": "cam-04",
            "name": "CAM-04 · NORTH PERIMETER",
            "sector": "SEC-4A",
            "sector_name": "SECTOR 4A · NORTH PERIMETER",
            "rtsp_url": "rtsp://192.168.4.108:554/live",
            "resolution": "4K · 30 FPS",
            "fps": 30,
            "lat": 31.4392,
            "lng": 74.3298
        }
    ]

    for cam in cameras_def:
        cam["status"] = "ALERT" if cam["id"].lower() in alerting_cams else "ONLINE"

    return cameras_def

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/detection")
async def receive_detection(payload: DetectionPayload, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    is_confirmed, reason = fusion_engine.process(payload)

    if is_confirmed:
        # Resolve zone and camera association
        zone_info = db.query(Zone).filter((Zone.zone_id == payload.zone_id) | (Zone.name == payload.zone_id)).first()
        
        # Sector Punjab border coordinate fallbacks (never hardcoded New Delhi)
        sector_coords = {
            "cam-01": (31.4385, 74.3210),
            "cam-02": (31.4398, 74.3245),
            "cam-03": (31.4421, 74.3270),
            "cam-04": (31.4392, 74.3298)
        }
        
        resolved_cam = (payload.camera_id or (zone_info.camera_id if zone_info else "cam-04")).lower()
        default_lat, default_lng = sector_coords.get(resolved_cam, (31.4392, 74.3298))
        
        lat = zone_info.lat if zone_info else default_lat
        lng = zone_info.lng if zone_info else default_lng
        zone_name = zone_info.name if zone_info else (payload.zone_id or "ZONE_A")

        thumbnail_url = ""
        if payload.frame_image:
            try:
                filename = f"alert_{int(datetime.utcnow().timestamp())}_{payload.track_id}.jpg"
                filepath = os.path.join(THUMBNAIL_DIR, filename)
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(payload.frame_image))
                thumbnail_url = f"/static/thumbnails/{filename}"
            except Exception as err:
                print(f"Failed to decode thumbnail: {err}")

        new_alert = AlertLog(
            object_class=payload.object_class,
            zone=zone_name,
            thumbnail=thumbnail_url,
            lat=lat,
            lng=lng,
            confidence=payload.confidence,
            status="PENDING",
            timestamp=datetime.utcnow()
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

        hardware_bridge.trigger_alert()

        alert_data = {
            "alert_id": new_alert.id,
            "object_class": new_alert.object_class,
            "zone": new_alert.zone,
            "zone_id": payload.zone_id or "ZONE_A",
            "camera_id": resolved_cam,
            "thumbnail": new_alert.thumbnail,
            "lat": new_alert.lat,
            "lng": new_alert.lng,
            "confidence": new_alert.confidence,
            "status": new_alert.status,
            "reason": reason,
            "timestamp": new_alert.timestamp.isoformat()
        }
        await manager.broadcast(alert_data)

        return {
            "status": "ALERT_CONFIRMED",
            "alert_id": new_alert.id,
            "camera_id": resolved_cam,
            "reason": reason,
            "thumbnail": thumbnail_url
        }

    return {"status": "FILTERED", "reason": reason}

@app.get("/alerts", response_model=List[AlertOut])
def get_alerts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    alerts = db.query(AlertLog).order_by(AlertLog.id.desc()).offset(skip).limit(limit).all()
    out = []
    for a in alerts:
        z = db.query(Zone).filter((Zone.zone_id == a.zone) | (Zone.name == a.zone)).first()
        out.append(AlertOut(
            alert_id=a.id,
            object_class=a.object_class,
            zone=a.zone,
            camera_id=z.camera_id.lower() if z and z.camera_id else "cam-04",
            thumbnail=a.thumbnail,
            lat=a.lat,
            lng=a.lng,
            confidence=a.confidence,
            status=getattr(a, "status", "PENDING"),
            timestamp=a.timestamp.isoformat()
        ))
    return out
 
@app.delete("/alerts")
async def clear_all_alerts(db: Session = Depends(get_db)):
    deleted_count = db.query(AlertLog).delete()
    db.commit()
    await manager.broadcast({"event_type": "ALERTS_CLEARED", "deleted_count": deleted_count})
    return {"status": "SUCCESS", "message": f"Cleared {deleted_count} alerts", "deleted_count": deleted_count}

@app.get("/videos")
def list_available_videos():
    videos = []
    if os.path.exists(MEDIA_DIR):
        for f in sorted(os.listdir(MEDIA_DIR)):
            if f.endswith((".mp4", ".avi", ".mkv", ".mov")):
                full_path = os.path.join(MEDIA_DIR, f)
                size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)
                
                lower_f = f.lower()
                if "river" in lower_f:
                    category = "RIVERINE"
                    badge = "🌊 Riverine Sector"
                elif "snow" in lower_f or "snowy" in lower_f:
                    category = "SNOW_PASS"
                    badge = "🏔️ Mountain Snow Pass"
                elif "dog" in lower_f or "animal" in lower_f:
                    category = "ANIMAL"
                    badge = "🐾 Wildlife Filter"
                elif "vehicle" in lower_f or "patrol" in lower_f:
                    category = "VEHICLE"
                    badge = "🚗 Border Patrol Unit"
                elif "wind" in lower_f or "grass" in lower_f or "empty" in lower_f:
                    category = "ENVIRONMENTAL"
                    badge = "💨 Environmental Wind"
                else:
                    category = "INTRUSION"
                    badge = "🚨 Tactical Intrusion"

                clean_title = f.replace("_", " ").replace(".mp4", "")
                if "WhatsApp Video" in clean_title:
                    clean_title = "Tactical Border Breach (" + clean_title.split("at")[-1].strip() + ")"
                
                videos.append({
                    "id": f,
                    "filename": f,
                    "title": clean_title,
                    "category": category,
                    "badge": badge,
                    "url": f"/videos/{f}",
                    "media_url": f"/media/{f}",
                    "size_mb": size_mb
                })
    return videos

@app.post("/dispatch", response_model=DispatchResponse)
async def dispatch_unit(
    req: DispatchRequest, 
    db: Session = Depends(get_db), 
    api_key: str = Depends(verify_api_key)
):
    eta_map = {
        "alpha": "2m (QRT Alpha)",
        "bravo": "5m (QRT Bravo)",
        "drone": "45s (UAV Drone Interceptor)"
    }
    eta = eta_map.get(req.unit_id.lower(), "3m (Tactical Unit)")
    dispatch_id = f"DSP-{int(datetime.utcnow().timestamp())}"
    now_iso = datetime.utcnow().isoformat()

    # Query alert by ID and update status to DISPATCHED
    alert = db.query(AlertLog).filter(AlertLog.id == req.alert_id).first()
    if alert:
        alert.status = "DISPATCHED"
        db.commit()
        db.refresh(alert)

    dispatch_event = {
        "event_type": "QRT_DISPATCHED",
        "dispatch_id": dispatch_id,
        "alert_id": req.alert_id,
        "unit_id": req.unit_id,
        "target_sector": req.target_sector,
        "eta": eta,
        "status": "DISPATCHED",
        "timestamp": now_iso
    }
    await manager.broadcast(dispatch_event)

    return DispatchResponse(
        status="DISPATCH_CONFIRMED",
        dispatch_id=dispatch_id,
        alert_id=req.alert_id,
        unit_id=req.unit_id,
        eta=eta,
        timestamp=now_iso
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)