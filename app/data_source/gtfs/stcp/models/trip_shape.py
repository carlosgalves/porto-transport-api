from sqlalchemy import Column, String
from app.core.database import Base


class TripShape(Base):
    __tablename__ = "trip_shapes"
    
    trip_id = Column(String, primary_key=True, index=True)
    shape_id = Column(String, nullable=False, index=True)