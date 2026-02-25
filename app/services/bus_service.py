import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings
from app.data_source.fiware.client import FIWAREClient
from app.data_source.fiware.parser import FIWAREParser
from app.data_source.gtfs.stcp.models.bus import Bus as BusModel
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.route_direction import RouteDirection as RouteDirectionModel
from app.api.schemas.bus import Bus, BusTrip, BusRoute, BusCoordinates


async def update_buses():
    Base.metadata.create_all(bind=engine)
    
    try:
        vehicles_data = await FIWAREClient.fetch_vehicles(limit=1000)
    except Exception as e:
        print(f"Error fetching vehicles: {e}")
        return
    
    parsed_buses = FIWAREParser.parse_vehicles(vehicles_data)
    
    def _delete_stale_buses(session: Session) -> int:
        cutoff = datetime.utcnow() - timedelta(minutes=settings.BUS_STALE_MINUTES)
        deleted = session.query(BusModel).filter(BusModel.last_updated < cutoff).delete()
        return deleted
    
    def _is_observation_stale(obs_dt: datetime) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.BUS_STALE_MINUTES)
        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=timezone.utc)
        else:
            obs_dt = obs_dt.astimezone(timezone.utc)
        return obs_dt < cutoff
    
    db: Session = SessionLocal()
    try:
        updated_count = 0
        inserted_count = 0
        
        for bus_data in parsed_buses:
            vehicle_id = bus_data["vehicle_id"]
            last_updated = bus_data.get("last_updated")
            
            if last_updated and _is_observation_stale(last_updated):
                existing = db.query(BusModel).filter(BusModel.vehicle_id == vehicle_id).first()
                if existing:
                    db.delete(existing)
                continue
            
            existing_bus = db.query(BusModel).filter(BusModel.vehicle_id == vehicle_id).first()
            
            if existing_bus:
                existing_bus.route_id = bus_data.get("route_id")
                existing_bus.direction_id = bus_data.get("direction_id")
                existing_bus.service_id = bus_data.get("service_id")
                existing_bus.lat = bus_data["lat"]
                existing_bus.lon = bus_data["lon"]
                existing_bus.heading = bus_data.get("heading")
                existing_bus.speed = bus_data.get("speed")
                existing_bus.last_updated = last_updated
                updated_count += 1
            else:
                new_bus = BusModel(
                    vehicle_id=vehicle_id,
                    route_id=bus_data.get("route_id"),
                    direction_id=bus_data.get("direction_id"),
                    service_id=bus_data.get("service_id"),
                    lat=bus_data["lat"],
                    lon=bus_data["lon"],
                    heading=bus_data.get("heading"),
                    speed=bus_data.get("speed"),
                    last_updated=last_updated
                )
                db.add(new_bus)
                inserted_count += 1
        
        deleted_count = _delete_stale_buses(db)
        db.commit()
        
    except Exception as e:
        print(f"Error updating buses: {e}")
        db.rollback()
    finally:
        db.close()


async def run_periodic_bus_updates(interval_seconds: int = 15):
    """Run periodic bus updates in the background."""
    while True:
        try:
            await update_buses()
            await asyncio.sleep(interval_seconds)
        except Exception as e:
            print(f"Error in periodic bus update: {e}")
            await asyncio.sleep(interval_seconds)


class BusService:
    
    @staticmethod
    def _model_to_schema(db_bus: BusModel, db: Session) -> Bus:
        trip = None
        route = None

        # FIWARE does not return the trip_number
        
        # get trip from route_id, direction_id, and service_id
        if db_bus.route_id and db_bus.direction_id is not None and db_bus.service_id:
            db_trip = db.query(TripModel).filter(
                and_(
                    TripModel.route_id == db_bus.route_id,
                    TripModel.direction_id == db_bus.direction_id,
                    TripModel.service_id == db_bus.service_id
                )
            ).first()
            
            if db_trip:
                # trip_id: route_id_direction_id_service_id
                trip_id_without_number = f"{db_bus.route_id}_{db_bus.direction_id}_{db_bus.service_id}"
                
                trip = BusTrip(
                    trip_id=trip_id_without_number,
                    service_id=db_trip.service_id,
                    trip_number=None,
                    headsign=db_trip.headsign,
                    wheelchair_accessible=db_trip.wheelchair_accessible
                )
        
        if db_bus.route_id and db_bus.direction_id is not None:
            route_direction_query = db.query(RouteDirectionModel).filter(
                and_(
                    RouteDirectionModel.route_id == db_bus.route_id,
                    RouteDirectionModel.direction_id == db_bus.direction_id
                )
            )
            
            if db_bus.service_id:
                route_direction_query = route_direction_query.filter(
                    RouteDirectionModel.service_id == db_bus.service_id
                )
            
            db_route_direction = route_direction_query.first()
            
            if db_route_direction:
                route = BusRoute(
                    route_id=db_bus.route_id,
                    headsign=db_route_direction.headsign,
                    direction=str(db_bus.direction_id)
                )
        
        coordinates = BusCoordinates(
            lat=db_bus.lat,
            lon=db_bus.lon,
            heading=db_bus.heading
        )
        
        return Bus(
            vehicle_id=db_bus.vehicle_id,
            trip=trip,
            route=route,
            coordinates=coordinates,
            speed=db_bus.speed,
            last_updated=db_bus.last_updated
        )
    
    @staticmethod
    def get_buses(
        db: Session,
        route_id: Optional[str] = None,
        direction_id: Optional[int] = None,
        page: int = 0,
        size: int = 100
    ) -> Tuple[List[Bus], int]:

        query = db.query(BusModel)
        
        filters = []
        
        if route_id:
            filters.append(BusModel.route_id == route_id)
        
        if direction_id is not None:
            # Only apply if route_id is also provided
            if route_id:
                filters.append(BusModel.direction_id == direction_id)
            # If route_id is not provided, direction_id is ignored
        
        if filters:
            query = query.filter(and_(*filters))
        
        total = query.count()
        
        skip = page * size
        db_buses = query.offset(skip).limit(size).all()
        
        buses = [BusService._model_to_schema(bus, db) for bus in db_buses]
        
        return buses, total
    
    @staticmethod
    def get_bus_by_id(db: Session, vehicle_id: str) -> Optional[Bus]:
        db_bus = db.query(BusModel).filter(BusModel.vehicle_id == vehicle_id).first()
        
        if db_bus:
            return BusService._model_to_schema(db_bus, db)
        return None