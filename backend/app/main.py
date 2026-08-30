from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from app.database import Base, engine, get_db
from app.models import AlertLog
from app.schemas import DetectionPayload, AlertOut
from app.fusion import fusion_engine
from app.hardware import hardware_bridge

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sima-Drishti Surveillance API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health")
def health_check():
    return {"status": "active", "service": "Sima-Drishti Backend", "timestamp": datetime.utcnow().isoformat()}

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
        # Save to SQLite
        new_alert = AlertLog(
            object_class=payload.object_class,
            zone="Sector_Alpha",
            thumbnail="",
            lat=28.7041,
            lng=77.1025,
            confidence=payload.confidence,
            timestamp=datetime.utcnow()
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

        # Trigger Physical Hardware
        hardware_bridge.trigger_alert()

        # Push payload to UI via WebSocket matching contract
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

        return {"status": "ALERT_CONFIRMED", "alert_id": new_alert.id, "reason": reason}

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