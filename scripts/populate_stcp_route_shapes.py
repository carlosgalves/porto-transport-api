import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.data_source.gtfs.stcp.models.route_shape import RouteShape
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.trip_shape import TripShape as TripShapeModel


def load_route_shapes():
    Base.metadata.create_all(bind=engine)
    
    print("Loading route_shapes from trips and trip_shapes tables...")
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(RouteShape).delete()
        
        # Get all unique route_id + direction_id combinations
        route_directions = db.query(
            TripModel.route_id,
            TripModel.direction_id
        ).distinct().all()
        
        route_shapes_list = []
        
        for route_id, direction_id in route_directions:
            # Get all trips for route+direction
            trips = db.query(TripModel.trip_id).filter(
                TripModel.route_id == route_id,
                TripModel.direction_id == direction_id
            ).all()
            
            if not trips:
                continue
            
            trip_ids = [trip.trip_id for trip in trips]
            
            # Get the shape_id for these trips (should be the same for all trips in same route+direction)
            trip_shape = db.query(TripShapeModel.shape_id).filter(
                TripShapeModel.trip_id.in_(trip_ids)
            ).first()
            
            if trip_shape:
                route_shapes_list.append(RouteShape(
                    route_id=route_id,
                    direction_id=direction_id,
                    shape_id=trip_shape.shape_id
                ))
        
        db.bulk_save_objects(route_shapes_list)
        db.commit()
        
        print(f"Successfully loaded {len(route_shapes_list)} route-shape relationships into database")
    except Exception as e:
        print(f"Error loading route_shapes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_route_shapes()