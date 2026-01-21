from sqlalchemy import Column, String, Integer, Time, Index
from app.core.database import Base


class ScheduledArrival(Base):
    __tablename__ = "scheduled_arrivals"
    
    trip_id = Column(String, primary_key=True, index=True)
    stop_id = Column(String, primary_key=True, index=True)
    stop_sequence = Column(Integer, primary_key=True, index=True)
    arrival_time = Column(Time, nullable=False)
    departure_time = Column(Time, nullable=False)