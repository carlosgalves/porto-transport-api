from sqlalchemy import Column, String, Integer
from app.core.database import Base


class TripStop(Base):
    __tablename__ = "trip_stops"
    
    trip_id = Column(String, primary_key=True, index=True)
    stop_id = Column(String, primary_key=True, index=True)
    sequence = Column(Integer, primary_key=True, index=True)