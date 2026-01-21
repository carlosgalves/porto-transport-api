from sqlalchemy import Column, String, Integer
from app.core.database import Base


class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
