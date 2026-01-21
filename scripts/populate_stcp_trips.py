import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.normalizer import GTFSNormalizer
from app.data_source.gtfs.stcp.models.trip import Trip


def load_trips():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading trips from {settings.GTFS_DATA_DIR}/trips.txt...")
    raw_trips = loader._load_csv_file("trips.txt")
    normalized_trips = GTFSNormalizer.normalize_trips_for_table(raw_trips)
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(Trip).delete()
        
        db_trips = [
            Trip(
                trip_id=trip["trip_id"],
                route_id=trip["route_id"],
                direction_id=trip["direction_id"],
                service_id=trip["service_id"],
                trip_number=trip["trip_number"],
                headsign=trip["headsign"],
                wheelchair_accessible=trip["wheelchair_accessible"]
            )
            for trip in normalized_trips
        ]
        
        db.bulk_save_objects(db_trips)
        db.commit()
        
        print(f"Successfully loaded {len(db_trips)} trips into database")
    except Exception as e:
        print(f"Error loading trips: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_trips()