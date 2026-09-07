import os
import base64
from datetime import datetime, timedelta
from typing import List
import json
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import Base, engine, get_db
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
    """Ensures DB schema compatibility and seeds default Punjab border zone if absent."""
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

    db = next(get_db())
    try:
        existing = db.query(Zone).filter((Zone.zone_id == "ZONE_A") | (Zone.name == "ZONE_A")).first()
        if not existing:
            default_zone = Zone(
                zone_id="ZONE_A",
                name="ZONE_A",
                camera_id="cam-04",
                lat=31.4392,
                lng=74.3298,
                radius_meters=500.0
            )
            db.add(default_zone)
            db.commit()
            print("[Database Seed] Seeded default zone: ZONE_A (Lat: 31.4392, Lng: 74.3298, Radius: 500m)")
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

@app.on_event("startup")
def startup_event():
    seed_default_zone()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

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
def list_cameras():
    return [
        {
            "id": "cam-01",
            "name": "CAM-01 · GATE ALPHA",
            "status": "ONLINE",
            "fps": 30,
            "sector": "SEC-1",
            "sector_name": "SECTOR 1A · GATEWAY ALPHA",
            "rtsp_url": "rtsp://192.168.1.101:554/ch01/main",
            "resolution": "1080P · 30 FPS",
            "lat": 31.4385,
            "lng": 74.3210
        },
        {
            "id": "cam-02",
            "name": "CAM-02 · FENCE BRAVO",
            "status": "ONLINE",
            "fps": 30,
            "sector": "SEC-2",
            "sector_name": "SECTOR 2B · FENCE PERIMETER BRAVO",
            "rtsp_url": "rtsp://192.168.2.102:554/ch01/main",
            "resolution": "2K · 30 FPS",
            "lat": 31.4398,
            "lng": 74.3245
        },
        {
            "id": "cam-03",
            "name": "CAM-03 · RIVERINE WATCH",
            "status": "ONLINE",
            "fps": 28,
            "sector": "SEC-3",
            "sector_name": "SECTOR 3C · RIVERINE EMBANKMENT",
            "rtsp_url": "rtsp://192.168.3.103:554/ch01/main",
            "resolution": "1080P · 28 FPS",
            "lat": 31.4421,
            "lng": 74.3270
        },
        {
            "id": "cam-04",
            "name": "CAM-04 · NORTH PERIMETER",
            "status": "ALERT",
            "fps": 30,
            "sector": "SEC-4A",
            "sector_name": "SECTOR 4A · NORTH PERIMETER",
            "rtsp_url": "rtsp://192.168.4.108:554/live",
            "resolution": "4K · 30 FPS",
            "lat": 31.4392,
            "lng": 74.3298
        }
    ]

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
        zone_info = db.query(Zone).filter(Zone.zone_id == payload.zone_id).first()
        lat = zone_info.lat if zone_info else 28.7041
        lng = zone_info.lng if zone_info else 77.1025
        zone_name = zone_info.name if zone_info else payload.zone_id

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
            "thumbnail": new_alert.thumbnail,
            "lat": new_alert.lat,
            "lng": new_alert.lng,
            "confidence": new_alert.confidence,
            "status": new_alert.status,
            "timestamp": new_alert.timestamp.isoformat()
        }
        await manager.broadcast(alert_data)

        return {"status": "ALERT_CONFIRMED", "alert_id": new_alert.id, "reason": reason, "thumbnail": thumbnail_url}

    return {"status": "FILTERED", "reason": reason}

@app.get("/alerts", response_model=List[AlertOut])
def get_alerts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    alerts = db.query(AlertLog).order_by(AlertLog.id.desc()).offset(skip).limit(limit).all()
    return [
        AlertOut(
            alert_id=a.id,
            object_class=a.object_class,
            zone=a.zone,
            thumbnail=a.thumbnail,
            lat=a.lat,
            lng=a.lng,
            confidence=a.confidence,
            status=getattr(a, "status", "PENDING"),
            timestamp=a.timestamp.isoformat()
        ) for a in alerts
    ]

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