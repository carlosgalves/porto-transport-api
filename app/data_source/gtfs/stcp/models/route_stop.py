from sqlalchemy import Column, String, Integer
from app.core.database import Base


class RouteStop(Base):
    __tablename__ = "route_stops"
    
    route_id = Column(String, primary_key=True, index=True)
    direction_id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(String, primary_key=True, index=True)
    stop_sequence = Column(Integer, nullable=False, index=True)