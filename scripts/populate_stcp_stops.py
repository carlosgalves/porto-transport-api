import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.stop import Stop as StopModel


def load_stops():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading stops from {settings.GTFS_DATA_DIR}/stops.txt...")
    stops_data = loader.load_stops()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(StopModel).delete()
        
        db_stops = [
            StopModel(
                id=stop["id"],
                name=stop["name"],
                lat=stop["lat"],
                lon=stop["lon"],
                zone_id=stop["zone_id"]
            )
            for stop in stops_data
        ]
        
        db.bulk_save_objects(db_stops)
        db.commit()
        
        print(f"Successfully loaded {len(db_stops)} stops into database")
    except Exception as e:
        print(f"Error loading stops: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_stops()
