from sqlalchemy import Column, String, Integer, Float, Time, DateTime
from datetime import datetime
from app.core.database import Base


class RealtimeArrival(Base):
    __tablename__ = "realtime_arrivals"
    
    # Composite primary key: vehicle_id + stop_id + trip_number uniquely identifies a real-time arrival
    # TODO: Fill vehicle_id
    
    vehicle_id = Column(String, primary_key=True, index=True)
    stop_id = Column(String, primary_key=True, index=True)
    trip_number = Column(String, primary_key=True, index=True)
    route_id = Column(String, nullable=False, index=True)
    direction_id = Column(Integer, nullable=False, index=True)
    service_id = Column(String, nullable=False, index=True)
    stop_sequence = Column(Integer, nullable=False, index=True)
    realtime_arrival_time = Column(Time, index=True)
    scheduled_arrival_time = Column(Time, index=True)
    arrival_minutes = Column(Float, nullable=True)
    delay_minutes = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)