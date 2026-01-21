from sqlalchemy import Column, String, Float
from app.core.database import Base


class Stop(Base):    
    __tablename__ = "stops"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    zone_id = Column(String, nullable=False)