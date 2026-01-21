from sqlalchemy import Column, String, Integer
from app.core.database import Base


class RouteShape(Base):
    __tablename__ = "route_shapes"
    
    route_id = Column(String, primary_key=True, index=True)
    direction_id = Column(Integer, primary_key=True, index=True)
    shape_id = Column(String, nullable=False, index=True)