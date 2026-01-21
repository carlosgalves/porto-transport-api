from sqlalchemy import Column, String, Integer
from app.core.database import Base


class RouteDirection(Base):
    __tablename__ = "route_directions"
    
    route_id = Column(String, primary_key=True, index=True)
    direction_id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, primary_key=True, index=True)
    headsign = Column(String, nullable=False)