import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.service_day import ServiceDay


def load_service_days():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading service days from {settings.GTFS_DATA_DIR}/calendar.txt...")
    service_days_data = loader.load_calendar()
    
    db: Session = SessionLocal()
    try:
        
        db_service_days = [
            ServiceDay(
                service_id=sd["service_id"],
                service_name=sd["service_name"],
                service_type=sd["service_type"],
                day_map=sd["day_map"],
                start_date=sd["start_date"],
                end_date=sd["end_date"]
            )
            for sd in service_days_data
        ]
        
        db.bulk_save_objects(db_service_days)
        db.commit()
        
        print(f"Successfully loaded {len(db_service_days)} service days into database")
    except Exception as e:
        print(f"Error loading service days: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_service_days()