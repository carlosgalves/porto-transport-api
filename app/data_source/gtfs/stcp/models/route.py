from sqlalchemy import Column, String, Integer
from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"
    
    id = Column(String, primary_key=True, index=True)
    short_name = Column(String, nullable=False)
    long_name = Column(String, nullable=False)
    type = Column(Integer, nullable=False)
    route_color = Column(String, nullable=False)
    route_text_color = Column(String, nullable=False)