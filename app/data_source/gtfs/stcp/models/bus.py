from sqlalchemy import Column, String, Float, DateTime, Integer
from datetime import datetime
from app.core.database import Base


class Bus(Base):
    __tablename__ = "buses"
    
    vehicle_id = Column(String, primary_key=True, index=True)
    route_id = Column(String, nullable=False, index=True)
    direction_id = Column(Integer, nullable=False)
    service_id = Column(String, nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)