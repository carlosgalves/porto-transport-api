from sqlalchemy import Column, String, Integer, Boolean, Index
from app.core.database import Base


class Trip(Base):
    __tablename__ = "trips"
    
    trip_id = Column(String, primary_key=True, index=True)
    route_id = Column(String, nullable=False, index=True)
    direction_id = Column(Integer, nullable=False, index=True)
    service_id = Column(String, nullable=False, index=True)
    trip_number = Column(String, nullable=False, index=True)
    headsign = Column(String, nullable=False)
    wheelchair_accessible = Column(Boolean, nullable=False, default=False)