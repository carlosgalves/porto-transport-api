import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.data_source.gtfs.stcp.models.route_stop import RouteStop
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.trip_stop import TripStop as TripStopModel
from app.data_source.gtfs.stcp.models.stop import Stop as StopModel


def load_route_stops():
    Base.metadata.create_all(bind=engine)

    print("Loading route_stops from trips, trip_stops and stops tables...")

    db: Session = SessionLocal()
    try:
        db.query(RouteStop).delete()

        # Stop id -> name
        stop_rows = db.query(StopModel.id, StopModel.name).all()
        stop_names = {row.id: row.name for row in stop_rows}

        route_directions = db.query(
            TripModel.route_id,
            TripModel.direction_id,
        ).distinct().all()

        route_stops_list = []
        unique_route_stops = {}

        for route_id, direction_id in route_directions:
            trips = db.query(
                TripModel.trip_id,
                TripModel.service_id,
            ).filter(
                TripModel.route_id == route_id,
                TripModel.direction_id == direction_id,
            ).all()

            if not trips:
                continue

            trip_ids = [t.trip_id for t in trips]
            trip_stop_rows = db.query(
                TripStopModel.trip_id,
                TripStopModel.stop_id,
                TripStopModel.sequence,
            ).filter(TripStopModel.trip_id.in_(trip_ids)).order_by(
                TripStopModel.trip_id,
                TripStopModel.sequence,
            ).all()

            # Group by trip_id, ordered (stop_id, sequence)
            stops_by_trip = defaultdict(list)
            for trip_id, stop_id, sequence in trip_stop_rows:
                stops_by_trip[trip_id].append((stop_id, sequence))

            # Build full headsign per trip and group by (service_id, stop_sequence_tuple)
            # key (service_id, tuple(stop_ids in order)) -> (headsign, list of (stop_sequence, stop_id))
            patterns = {}
            for trip_id, service_id in trips:
                ordered = stops_by_trip.get(trip_id, [])
                if not ordered:
                    continue
                stop_ids_ordered = tuple(s[0] for s in ordered)
                first_stop_id = ordered[0][0]
                last_stop_id = ordered[-1][0]
                first_name = stop_names.get(first_stop_id, first_stop_id)
                last_name = stop_names.get(last_stop_id, last_stop_id)
                headsign = f"{first_name} - {last_name}"
                key = (service_id, stop_ids_ordered)
                if key not in patterns:
                    patterns[key] = (headsign, ordered)

            for (service_id, _), (headsign, ordered) in patterns.items():
                for stop_id, stop_sequence in ordered:
                    key = (route_id, direction_id, headsign, service_id, stop_sequence)
                    if key not in unique_route_stops:
                        unique_route_stops[key] = RouteStop(
                            route_id=route_id,
                            direction_id=direction_id,
                            headsign=headsign,
                            service_id=service_id,
                            stop_sequence=stop_sequence,
                            stop_id=stop_id,
                        )

        route_stops_list = list(unique_route_stops.values())

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
