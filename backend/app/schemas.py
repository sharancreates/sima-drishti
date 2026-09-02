from pydantic import BaseModel
from typing import List, Optional

class DetectionPayload(BaseModel):
    object_class: str
    confidence: float
    bbox: List[float]
    track_id: int
    in_zone: bool
    timestamp: float
    frame_image: Optional[str] = None  # Base64 encoded JPEG for alert thumbnail

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