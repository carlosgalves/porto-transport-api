from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.data_source.gtfs.stcp.models.stop import Stop as StopModel
from app.data_source.gtfs.stcp.models.scheduled_arrival import ScheduledArrival as ScheduledArrivalModel
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.stcp.client import STCPClient
from app.data_source.stcp.parser import STCPParser
from app.api.schemas.stop import Stop
from app.api.schemas.shared import Coordinates
from app.api.schemas.arrival import (
    ScheduledArrival, TripInfo, StopInfo,
    RealtimeArrival,
)


class StopService:
    
    @staticmethod
    def _model_to_schema(db_stop: StopModel) -> Stop:
        return Stop(
            id=db_stop.id,
            name=db_stop.name,
            coordinates=Coordinates(
                latitude=db_stop.lat,
                longitude=db_stop.lon
            ),
            zone_id=db_stop.zone_id
        )
    
    @staticmethod
    def get_stop_by_id(db: Session, stop_id: str) -> Optional[Stop]:
        db_stop = db.query(StopModel).filter(StopModel.id == stop_id).first()
        if db_stop:
            return StopService._model_to_schema(db_stop)
        return None
    
    @staticmethod
    def get_stops(
        db: Session, 
        zone_id: Optional[str] = None,
        page: int = 0,
        size: Optional[int] = 100
    ) -> Tuple[List[Stop], int]:

        query = db.query(StopModel)
        
        if zone_id:
            query = query.filter(StopModel.zone_id == zone_id)
        
        total = query.count()
        
        # If no size is provided, return all stops without pagination
        if size is None:
            db_stops = query.all()
        else:
            skip = page * size
            db_stops = query.offset(skip).limit(size).all()
        
        stops = [StopService._model_to_schema(stop) for stop in db_stops]
        return stops, total
    
    @staticmethod
    def get_scheduled_arrivals(
        db: Session,
        stop_id: str,
        route_id: Optional[str] = None,
        service_id: Optional[str] = None,
        service_id_dates: Optional[Dict[str, List[date]]] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        page: int = 0,
        size: int = 100
    ) -> Tuple[List[ScheduledArrival], int]:

        # Join with trips table to get route_id, direction_id, service_id, trip_number
        query = db.query(ScheduledArrivalModel).join(
            TripModel, ScheduledArrivalModel.trip_id == TripModel.trip_id
        ).filter(
            ScheduledArrivalModel.stop_id == stop_id
        )
        
        # Apply optional filters
        if route_id is not None:
            query = query.filter(TripModel.route_id == route_id)
        
        if service_id is not None:
            query = query.filter(TripModel.service_id == service_id)
        elif service_id_dates:
            query = query.filter(TripModel.service_id.in_(list(service_id_dates.keys())))

        if not window_start or not window_end:
            total = query.count()
            skip = page * size
            arrivals = query.order_by(ScheduledArrivalModel.arrival_time).offset(skip).limit(size).all()

            # Convert to schema with trip and stop info
            result = []
            for arrival in arrivals:
                trip = db.query(TripModel).filter(TripModel.trip_id == arrival.trip_id).first()
                if trip:
                    trip_info = TripInfo(
                        id=arrival.trip_id,
                        route_id=trip.route_id,
                        direction_id=trip.direction_id,
                        service_id=trip.service_id,
                        number=trip.trip_number,
                        headsign=trip.headsign
                    )

                    stop_info = StopInfo(
                        id=arrival.stop_id,
                        sequence=arrival.stop_sequence
                    )

                    scheduled_arrival = ScheduledArrival(
                        trip=trip_info,
                        stop=stop_info,
                        arrival_time=arrival.arrival_time,
                        departure_time=arrival.departure_time
                    )
                    result.append(scheduled_arrival)

            return result, total


        arrivals = query.all()

        service_id_dates = service_id_dates or {}
        if service_id is not None:
            service_id_dates.setdefault(service_id, [window_start.date(), window_end.date()])

        candidates: List[tuple[datetime, ScheduledArrival]] = []

        for arrival in arrivals:
            trip = db.query(TripModel).filter(TripModel.trip_id == arrival.trip_id).first()
            if not trip:
                continue

            trip_info = TripInfo(
                id=arrival.trip_id,
                route_id=trip.route_id,
                direction_id=trip.direction_id,
                service_id=trip.service_id,
                number=trip.trip_number,
                headsign=trip.headsign
            )

            stop_info = StopInfo(
                id=arrival.stop_id,
                sequence=arrival.stop_sequence
            )

            scheduled_arrival = ScheduledArrival(
                trip=trip_info,
                stop=stop_info,
                arrival_time=arrival.arrival_time,
                departure_time=arrival.departure_time
            )

            dates_for_service = service_id_dates.get(trip.service_id, [])
            for d in dates_for_service:
                dt = datetime.combine(d, arrival.arrival_time)
                if window_start <= dt <= window_end:
                    candidates.append((dt, scheduled_arrival))

        candidates.sort(key=lambda x: x[0])
        total = len(candidates)

        start = page * size
        end = start + size
        page_items = [item for _, item in candidates[start:end]]
        return page_items, total
    
    @staticmethod
    def calculate_scheduled_arrival_time(arrival_time: Optional[time], delay_minutes: Optional[int]) -> Optional[time]:
        # scheduled_arrival_time = arrival_time - delay_minutes
        if arrival_time is None or delay_minutes is None:
            return None
        
        try:
            arrival_dt = datetime.combine(datetime.today(), arrival_time)
            scheduled_dt = arrival_dt - timedelta(minutes=delay_minutes)
            return scheduled_dt.time()
        except (ValueError, TypeError, OverflowError):
            return None

    @staticmethod
    def find_matching_scheduled_arrival(
        db: Session,
        stop_id: str,
        route_id: str,
        direction_id: int,
        service_id: str,
        scheduled_arrival_time: Optional[time]
    ) -> Optional[dict]:
        
        if scheduled_arrival_time is None:
            return None
        
        target_seconds = scheduled_arrival_time.hour * 3600 + scheduled_arrival_time.minute * 60 + scheduled_arrival_time.second
        
        # Join with trips table to filter by route_id, direction_id, service_id
        scheduled_arrivals = db.query(ScheduledArrivalModel).join(
            TripModel, ScheduledArrivalModel.trip_id == TripModel.trip_id
        ).filter(
            and_(
                TripModel.route_id == route_id,
                TripModel.direction_id == direction_id,
                TripModel.service_id == service_id,
                ScheduledArrivalModel.stop_id == stop_id
            )
        ).all()
        
        best_match = None
        min_diff = float('inf')
        
        for scheduled in scheduled_arrivals:
            scheduled_seconds = scheduled.arrival_time.hour * 3600 + scheduled.arrival_time.minute * 60 + scheduled.arrival_time.second
            diff = abs(scheduled_seconds - target_seconds)
            
            # find a trip that is within 1 minute of the scheduled arrival time
            if diff <= 60 and diff < min_diff:
                min_diff = diff
                best_match = scheduled
        
        if best_match:
            trip = db.query(TripModel).filter(TripModel.trip_id == best_match.trip_id).first()
            if trip:
                return {
                    "trip_number": trip.trip_number,
                    "stop_sequence": best_match.stop_sequence
                }
        
        return None

    @staticmethod
    async def get_realtime_arrivals_response(db: Session, stop_id: str) -> Optional[Tuple[List[RealtimeArrival], int]]:
        stop = db.query(StopModel).filter(StopModel.id == stop_id).first()
        if not stop:
            return None

        # Fetch real-time data from API
        stop_realtime_data = await STCPClient.fetch_stop_realtime(stop_id)
        if not stop_realtime_data:
            return ([], 0)

        parsed_arrivals = STCPParser.parse_stop_realtime(stop_realtime_data)

        last_updated_str = stop_realtime_data.get("last_updated")
        if last_updated_str:
            try:
                last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                last_updated = datetime.utcnow()
        else:
            last_updated = datetime.utcnow()

        arrival_items: List[RealtimeArrival] = []
        for arrival_data in parsed_arrivals:
            route_id = arrival_data["route_id"]
            direction_id = arrival_data["direction_id"]
            service_id = arrival_data["service_id"]
            arrival_time = arrival_data["arrival_time"]
            delay_minutes = arrival_data["delay_minutes"]

            scheduled_arrival_time = StopService.calculate_scheduled_arrival_time(arrival_time, delay_minutes)

            trip_number = arrival_data["trip_number"]
            stop_sequence = arrival_data["stop_sequence"]
            if scheduled_arrival_time:
                match = StopService.find_matching_scheduled_arrival(
                    db=db,
                    stop_id=stop_id,
                    route_id=route_id,
                    direction_id=direction_id,
                    service_id=service_id,
                    scheduled_arrival_time=scheduled_arrival_time
                )
                if match:
                    trip_number = match["trip_number"]
                    stop_sequence = match["stop_sequence"]

            trip_id = f"{route_id}_{direction_id}_{service_id}_{trip_number}"
            trip_info = TripInfo(
                id=trip_id,
                route_id=route_id,
                direction_id=direction_id,
                service_id=service_id,
                number=trip_number,
                headsign=arrival_data.get("trip_headsign")
            )
            stop_info = StopInfo(
                id=stop_id,
                sequence=stop_sequence
            )

            arrival_items.append(RealtimeArrival(
                vehicle_id=arrival_data["vehicle_id"],
                trip=trip_info,
                stop=stop_info,
                realtime_arrival_time=arrival_time,
                scheduled_arrival_time=scheduled_arrival_time,
                arrival_minutes=arrival_data["arrival_minutes"],
                delay_minutes=delay_minutes,
                status=arrival_data["status"],
                last_updated=last_updated
            ))

        arrival_items.sort(key=lambda x: (
            x.arrival_minutes if x.arrival_minutes is not None else float('inf'),
            x.realtime_arrival_time if x.realtime_arrival_time else time.max
        ))

        return (arrival_items, len(arrival_items))