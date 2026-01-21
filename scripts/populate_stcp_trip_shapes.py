import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.trip_shape import TripShape


def load_trip_shapes():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading trip_shapes from {settings.GTFS_DATA_DIR}/trips.txt...")
    trip_shapes_data = loader.load_trip_shapes()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(TripShape).delete()
        
        db_trip_shapes = [
            TripShape(
                trip_id=trip_shape["trip_id"],
                shape_id=trip_shape["shape_id"]
            )
            for trip_shape in trip_shapes_data
        ]
        
        db.bulk_save_objects(db_trip_shapes)
        db.commit()
        
        print(f"Successfully loaded {len(db_trip_shapes)} trip-shape relationships into database")
    except Exception as e:
        print(f"Error loading trip_shapes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_trip_shapes()