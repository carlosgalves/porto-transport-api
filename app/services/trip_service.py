from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.trip_shape import TripShape as TripShapeModel
from app.data_source.gtfs.stcp.models.trip_stop import TripStop as TripStopModel
from app.data_source.gtfs.stcp.models.stop import Stop as StopModel
from app.data_source.gtfs.stcp.models.shape import Shape as ShapeModel
from app.api.schemas.trip import Trip, TripInfo, TripStop, TripStopStopInfo
from app.api.schemas.shape import ShapePoint, TripShapesResponse
from app.api.schemas.shared import Coordinates


class TripService:
    
    @staticmethod
    def _model_to_schema(db_trip: TripModel) -> Trip:
        return Trip(
            trip=TripInfo(
                id=db_trip.trip_id,
                route_id=db_trip.route_id,
                direction_id=db_trip.direction_id,
                service_id=db_trip.service_id,
                number=db_trip.trip_number
            ),
            headsign=db_trip.headsign,
            wheelchair_accessible=bool(db_trip.wheelchair_accessible)
        )
    
    @staticmethod
    def get_trips(
        db: Session,
        route_id: Optional[str] = None,
        service_id: Optional[str] = None,
        direction_id: Optional[int] = None,
        wheelchair_accessible: Optional[int] = None,
        page: int = 0,
        size: int = 100
    ) -> tuple[List[Trip], int]:

        query = db.query(TripModel)
        
        filters = []
        
        if route_id:
            filters.append(TripModel.route_id == route_id)
        
        if service_id:
            service_ids = [sid.strip() for sid in service_id.split(",") if sid.strip()]
            if service_ids:
                filters.append(TripModel.service_id.in_(service_ids))
        
        if direction_id is not None:
            # Only apply if route_id is also provided
            if route_id:
                filters.append(TripModel.direction_id == direction_id)
            # If route_id is not provided, direction_id is ignored
        
        if wheelchair_accessible is not None:
            filters.append(TripModel.wheelchair_accessible == wheelchair_accessible)
        
        if filters:
            query = query.filter(and_(*filters))
        
        total = query.count()
        
        skip = page * size
        db_trips = query.offset(skip).limit(size).all()
        
        trips = [TripService._model_to_schema(trip) for trip in db_trips]
        
        return trips, total

    @staticmethod
    def get_trip_by_trip_id(db: Session, trip_id: str) -> Optional[Trip]:

        db_trip = db.query(TripModel).filter(TripModel.trip_id == trip_id).first()
        
        if db_trip:
            return TripService._model_to_schema(db_trip)
        return None

    @staticmethod
    def _shape_point_model_to_schema(db_shape: ShapeModel) -> ShapePoint:
        return ShapePoint(
            sequence=db_shape.sequence,
            coordinates=Coordinates(
                latitude=db_shape.lat,
                longitude=db_shape.lon
            )
        )

    @staticmethod
    def get_trip_shapes(db: Session, trip_id: str) -> Optional[TripShapesResponse]:

        # Get shape_id for this trip_id
        trip_shape = db.query(TripShapeModel).filter(
            TripShapeModel.trip_id == trip_id
        ).first()
        
        if not trip_shape:
            return None
        
        # Get all shape points for this shape_id, ordered by sequence
        db_shapes = db.query(ShapeModel).filter(
            ShapeModel.id == trip_shape.shape_id
        ).order_by(ShapeModel.sequence).all()
        
        points = [TripService._shape_point_model_to_schema(shape) for shape in db_shapes]
        
        return TripShapesResponse(
            trip_id=trip_id,
            shape_id=trip_shape.shape_id,
            points=points
        )

    @staticmethod
    def get_trip_stops(db: Session, trip_id: str) -> List[TripStop]:
        db_trip = db.query(TripModel).filter(TripModel.trip_id == trip_id).first()
        if not db_trip:
            return []
        
        results = db.query(
            TripStopModel,
            StopModel.name,
            StopModel.zone_id
        ).join(
            StopModel, TripStopModel.stop_id == StopModel.id
        ).filter(
            TripStopModel.trip_id == trip_id
        ).order_by(TripStopModel.sequence).all()
        
        return [
            TripStop(
                trip_id=ts.trip_id,
                stop=TripStopStopInfo(
                    id=ts.stop_id,
                    name=stop_name,
                    zone_id=zone_id
                ),
                sequence=ts.sequence
            )
            for ts, stop_name, zone_id in results
        ]