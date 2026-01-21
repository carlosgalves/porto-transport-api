import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.data_source.gtfs.stcp.models.route_stop import RouteStop
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.trip_stop import TripStop as TripStopModel


def load_route_stops():
    Base.metadata.create_all(bind=engine)
    
    print("Loading route_stops from trips and trip_stops tables...")
    
    db: Session = SessionLocal()
    try:
        # Clear old data
        db.query(RouteStop).delete()
        
        # Get all unique route_id + direction_id combinations
        route_directions = db.query(
            TripModel.route_id,
            TripModel.direction_id
        ).distinct().all()
        
        route_stops_list = []
        
        for route_id, direction_id in route_directions:
            # Get all trips for this route+direction
            trips = db.query(TripModel.trip_id).filter(
                TripModel.route_id == route_id,
                TripModel.direction_id == direction_id
            ).all()
            
            if not trips:
                continue
            
            trip_ids = [trip.trip_id for trip in trips]
            
            # Get unique stop_ids with their sequences for these trips
            # sequence is the same for same route+direction+stop
            trip_stops = db.query(
                TripStopModel.stop_id,
                TripStopModel.sequence
            ).filter(
                TripStopModel.trip_id.in_(trip_ids)
            ).distinct().all()
            
            # Group by stop_id and take the first sequence
            stop_sequences = {}
            for stop_id, sequence in trip_stops:
                if stop_id not in stop_sequences:
                    stop_sequences[stop_id] = sequence
            
            # Add route_stop entries for each unique stop with its sequence
            for stop_id, sequence in stop_sequences.items():
                route_stops_list.append(RouteStop(
                    route_id=route_id,
                    direction_id=direction_id,
                    stop_id=stop_id,
                    stop_sequence=sequence
                ))
        
        db.bulk_save_objects(route_stops_list)
        db.commit()
        
        print(f"Successfully loaded {len(route_stops_list)} route-stop relationships into database")
    except Exception as e:
        print(f"Error loading route_stops: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_route_stops()