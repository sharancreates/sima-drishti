import os
import base64
from datetime import datetime
from typing import List
import json
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import AlertLog, Zone
from app.schemas import DetectionPayload, AlertOut, ZoneCreate, ZoneOut
from app.fusion import fusion_engine
from app.hardware import hardware_bridge
from app.utils import cleanup_old_thumbnails

Base.metadata.create_all(bind=engine)

THUMBNAIL_DIR = "static/thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    cleanup_old_thumbnails()
    yield
    # Shutdown tasks (if any)

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
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

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

@app.post("/zones", response_model=ZoneOut)
def create_zone(zone_in: ZoneCreate, db: Session = Depends(get_db)):
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

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/detection")
async def receive_detection(payload: DetectionPayload, db: Session = Depends(get_db)):
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
            timestamp=a.timestamp.isoformat()
        ) for a in alerts
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)