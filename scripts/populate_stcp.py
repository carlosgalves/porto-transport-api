import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.gtfs.loader import GTFSLoader
from app.data_source.gtfs.stcp.models.agency import Agency
from scripts.populate_stcp_stops import load_stops
from scripts.populate_stcp_service_days import load_service_days
from scripts.populate_stcp_routes import load_all as load_routes_all
from scripts.populate_stcp_trips import load_trips
from scripts.populate_stcp_shapes import load_shapes
from scripts.populate_stcp_trip_shapes import load_trip_shapes
from scripts.populate_stcp_route_shapes import load_route_shapes
from scripts.populate_stcp_route_stops import load_route_stops
from scripts.populate_stcp_trip_stops import load_trip_stops
from scripts.populate_stcp_scheduled_arrivals import load_scheduled_arrivals


def load_agency():
    Base.metadata.create_all(bind=engine)
    
    loader = GTFSLoader(settings.GTFS_DATA_DIR)
    
    print(f"Loading agency from {settings.GTFS_DATA_DIR}/agency.txt...")
    agencies_data = loader.load_agency()
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(Agency).delete()
        
        agency_data = agencies_data[0]
        db_agency = Agency(
            id=agency_data["id"],
            name=agency_data["name"],
            url=agency_data["url"]
        )
        
        db.add(db_agency)
        db.commit()
        
        print(f"Successfully loaded agency into database")
    except Exception as e:
        print(f"Error loading agency: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def populate_all():
    print("=" * 60)
    print("Starting STCP GTFS data population")
    print("=" * 60)
    print()
    
    try:
        steps = 11
        
        # Agency
        print(f"Step 1/{steps}: Loading agencies...")
        load_agency()
        print()
        
        # Stops
        print(f"Step 2/{steps}: Loading stops...")
        load_stops()
        print()
        
        # Service days
        print(f"Step 3/{steps}: Loading service days...")
        load_service_days()
        print()
        
        # Routes
        print(f"Step 4/{steps}: Loading routes and directions...")
        load_routes_all()
        print()
        
        # Shapes
        print(f"Step 5/{steps}: Loading shapes...")
        load_shapes()
        print()
        
        # Trips
        print(f"Step 6/{steps}: Loading trips...")
        load_trips()
        print()
        
        # Trip shapes
        print(f"Step 7/{steps}: Loading trip shapes...")
        load_trip_shapes()
        print()
        
        # Route shapes
        print(f"Step 8/{steps}: Loading route shapes...")
        load_route_shapes()
        print()
        
        # Route stops
        print(f"Step 9/{steps}: Loading route stops...")
        load_route_stops()
        print()
        
        # Trip stops
        print(f"Step 10/{steps}: Loading trip stops...")
        load_trip_stops()
        print()
        
        # Scheduled arrivals
        print(f"Step 11/{steps}: Loading scheduled arrivals...")
        load_scheduled_arrivals()
        print()
        
        print("=" * 60)
        print("✓ All STCP GTFS data successfully populated!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Error during population: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    populate_all()
