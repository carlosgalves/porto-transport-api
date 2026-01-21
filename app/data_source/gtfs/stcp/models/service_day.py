from sqlalchemy import Column, String, Integer, Date
from app.core.database import Base


class ServiceDay(Base):
    __tablename__ = "service_days"
    
    service_id = Column(String, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    service_type = Column(Integer, nullable=True)
    day_map = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)