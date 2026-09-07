from pydantic import BaseModel
from typing import List, Optional

class ZoneCreate(BaseModel):
    zone_id: str
    name: str
    camera_id: str
    lat: float
    lng: float
    radius_meters: Optional[float] = 500.0

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
    confidence: float
    status: str = "PENDING"
    timestamp: str

    class Config:
        from_attributes = True

class DispatchRequest(BaseModel):
    alert_id: int
    unit_id: str
    target_sector: Optional[str] = "Sector 04-North"
    notes: Optional[str] = ""

class DispatchResponse(BaseModel):
    status: str
    dispatch_id: str
    alert_id: int
    unit_id: str
    eta: str
    timestamp: str