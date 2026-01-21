import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.route import Route
from app.data_source.gtfs.stcp.models.route_direction import RouteDirection


def load_routes():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading routes from {settings.GTFS_DATA_DIR}/routes.txt...")
    routes_data = loader.load_routes()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(Route).delete()
        
        db_routes = [
            Route(
                id=route["id"],
                short_name=route["short_name"],
                long_name=route["long_name"],
                type=route["type"],
                route_color=route["route_color"],
                route_text_color=route["route_text_color"]
            )
            for route in routes_data
        ]
        
        db.bulk_save_objects(db_routes)
        db.commit()
        
        print(f"Successfully loaded {len(db_routes)} routes into database")
    except Exception as e:
        print(f"Error loading routes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def load_route_directions():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading trips from {settings.GTFS_DATA_DIR}/trips.txt...")
    trips_data = loader.load_trips()
    
    seen = set()
    unique_directions = []
    for trip in trips_data:
        key = (trip["route_id"], trip["direction_id"], trip["service_id"])
        if key not in seen:
            seen.add(key)
            unique_directions.append(trip)
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(RouteDirection).delete()
        
        db_route_directions = [
            RouteDirection(
                route_id=rd["route_id"],
                direction_id=rd["direction_id"],
                service_id=rd["service_id"],
                headsign=rd["headsign"]
            )
            for rd in unique_directions
        ]
        
        db.bulk_save_objects(db_route_directions)
        db.commit()
        
        print(f"Successfully loaded {len(db_route_directions)} route directions into database")
        print("\n")
    except Exception as e:
        print(f"Error loading route directions: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def load_all():
    load_routes()
    load_route_directions()


if __name__ == "__main__":
    load_all()
