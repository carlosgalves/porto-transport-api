import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.trip_stop import TripStop


def load_trip_stops():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading stop_times from {settings.GTFS_DATA_DIR}/stop_times.txt...")
    raw_stop_times = loader.load_stop_times()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(TripStop).delete()
        
        trip_stops_list = [
            TripStop(
                trip_id=stop_time["trip_id"],
                stop_id=stop_time["stop_id"],
                sequence=stop_time["stop_sequence"]
            )
            for stop_time in raw_stop_times
        ]
        
        db.bulk_save_objects(trip_stops_list)
        db.commit()
        
        print(f"Successfully loaded {len(trip_stops_list)} trip-stop relationships into database")
    except Exception as e:
        print(f"Error loading trip_stops: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_trip_stops()