import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.scheduled_arrival import ScheduledArrival


def load_scheduled_arrivals():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading stop_times from {settings.GTFS_DATA_DIR}/stop_times.txt...")
    normalized_arrivals = loader.load_stop_times()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(ScheduledArrival).delete()
        
        db_arrivals = [
            ScheduledArrival(
                trip_id=arrival["trip_id"],
                stop_id=arrival["stop_id"],
                stop_sequence=arrival["stop_sequence"],
                arrival_time=arrival["arrival_time"],
                departure_time=arrival["departure_time"]
            )
            for arrival in normalized_arrivals
        ]
        
        db.bulk_save_objects(db_arrivals)
        db.commit()
        
        print(f"Successfully loaded {len(db_arrivals)} scheduled arrivals into database")
    except Exception as e:
        print(f"Error loading scheduled arrivals: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_scheduled_arrivals()