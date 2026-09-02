import os
import base64
from datetime import datetime
from typing import List
import json
import uvicorn

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import AlertLog
from app.schemas import DetectionPayload, AlertOut
from app.fusion import fusion_engine
from app.hardware import hardware_bridge

# Ensure SQLite schema is updated
Base.metadata.create_all(bind=engine)

# Ensure thumbnails directory exists
THUMBNAIL_DIR = "static/thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

app = FastAPI(
    title="Sima-Drishti Surveillance API",
    version="1.0.0"
)

# Enable CORS for React/Vite development server (usually port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder so UI can load thumbnails via URL
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

@app.get("/health")
def health_check():
    return {
        "status": "active",
        "service": "Sima-Drishti Backend",
        "active_ws_clients": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/detection")
async def receive_detection(payload: DetectionPayload, db: Session = Depends(get_db)):
    is_confirmed, reason = fusion_engine.process(payload)

    if is_confirmed:
        thumbnail_url = ""
        # If AI sends base64 frame thumbnail, decode and store it locally
        if payload.frame_image:
            try:
                filename = f"alert_{int(datetime.utcnow().timestamp())}_{payload.track_id}.jpg"
                filepath = os.path.join(THUMBNAIL_DIR, filename)
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(payload.frame_image))
                thumbnail_url = f"/static/thumbnails/{filename}"
            except Exception as err:
                print(f"Failed to decode thumbnail: {err}")

        # Save to SQLite
        new_alert = AlertLog(
            object_class=payload.object_class,
            zone="Sector_Alpha",
            thumbnail=thumbnail_url,
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

        # Push to UI clients via WebSocket matching contract exactly
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