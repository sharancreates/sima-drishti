from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetectionPayload(BaseModel):
    object_class: str
    confidence: float
    bbox: List[float]
    track_id: int
    in_zone: bool
    timestamp: float

class AlertOut(BaseModel):
    alert_id: int
    object_class: str
    zone: str
    thumbnail: str
    lat: float
    lng: float
    timestamp: str

    class Config:
        from_attributes = True