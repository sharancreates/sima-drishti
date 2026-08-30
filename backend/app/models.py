from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base

class AlertLog(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    object_class = Column(String, index=True, nullable=False)
    zone = Column(String, default="Sector_Alpha")
    thumbnail = Column(String, default="")
    lat = Column(Float, default=28.7041)
    lng = Column(Float, default=77.1025)
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)