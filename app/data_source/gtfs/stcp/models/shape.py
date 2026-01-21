from sqlalchemy import Column, String, Float, Integer
from app.core.database import Base


class Shape(Base):
    __tablename__ = "shapes"
    
    id = Column(String, primary_key=True, index=True)
    sequence = Column(Integer, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)