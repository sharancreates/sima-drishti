from pydantic import BaseModel
from typing import List, Optional

class ZoneCreate(BaseModel):
    zone_id: str
    name: str
    camera_id: str
    lat: float
    lng: float

class ZoneOut(ZoneCreate):
    id: int

    class Config:
        from_attributes = True

class DetectionPayload(BaseModel):
    object_class: str
    confidence: float
    bbox: List[float]
    track_id: int
    in_zone: bool
    timestamp: float
    zone_id: Optional[str] = "Sector_Alpha"
    frame_image: Optional[str] = None

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