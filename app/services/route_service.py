from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from app.data_source.gtfs.stcp.models.route import Route as RouteModel
from app.data_source.gtfs.stcp.models.route_direction import RouteDirection as RouteDirectionModel
from app.data_source.gtfs.stcp.models.route_shape import RouteShape as RouteShapeModel
from app.data_source.gtfs.stcp.models.route_stop import RouteStop as RouteStopModel
from app.data_source.gtfs.stcp.models.stop import Stop as StopModel
from app.data_source.gtfs.stcp.models.shape import Shape as ShapeModel
from app.data_source.gtfs.stcp.models.trip import Trip as TripModel
from app.data_source.gtfs.stcp.models.trip_stop import TripStop as TripStopModel
from app.api.schemas.route import Route, RouteDirectionItem, RouteStop, RouteStopRouteInfo, RouteStopStopInfo
from app.api.schemas.route_direction import RouteDirection
from app.api.schemas.shape import RouteShape, ShapePoint
from app.api.schemas.shared import Coordinates


class RouteService:
    
    @staticmethod
    def _model_to_schema(db_route: RouteModel, db: Session, include_service_days: bool = True) -> Route:
        route = Route(
            id=db_route.id,
            short_name=db_route.short_name,
            long_name=db_route.long_name,
            type=db_route.type,
            route_color=db_route.route_color,
            route_text_color=db_route.route_text_color
        )
        
        if include_service_days:
            service_ids = db.query(RouteDirectionModel.service_id).filter(
                RouteDirectionModel.route_id == db_route.id
            ).distinct().all()
            
            route.service_days = [service_id for (service_id,) in service_ids]
        
        return route
    
    @staticmethod
    def get_route_by_id(
        db: Session, 
        route_id: str, 
        include_directions: bool = True,
        service_ids: Optional[List[str]] = None
    ) -> Optional[Route]:
        db_route = db.query(RouteModel).filter(RouteModel.id == route_id).first()
        if db_route:
            route = RouteService._model_to_schema(db_route, db=db, include_service_days=True)
            if include_directions:
                directions = RouteService.get_route_directions(
                    db=db,
                    route_id=route_id,
                    service_ids=service_ids
                )
                
                direction_map: Dict[Tuple[str, int], List[str]] = defaultdict(list)
                for direction in directions:
                    key = (direction.headsign, direction.direction_id)
                    if direction.service_id not in direction_map[key]:
                        direction_map[key].append(direction.service_id)
                
                route.directions = [
                    RouteDirectionItem(
                        headsign=headsign,
                        direction_id=direction_id,
                        service_days=sorted(service_days)
                    )
                    for (headsign, direction_id), service_days in sorted(direction_map.items())
                ]
            return route
        return None
    
    @staticmethod
    def get_routes(
        db: Session, 
        service_ids: Optional[List[str]] = None,
        page: int = 0,
        size: int = 100
    ) -> tuple[List[Route], int]:

        query = db.query(RouteModel)
        
        if service_ids:
            route_ids = [
                rd.route_id for rd in db.query(RouteDirectionModel.route_id).filter(
                    RouteDirectionModel.service_id.in_(service_ids)
                ).distinct().all()
            ]
            query = query.filter(RouteModel.id.in_(route_ids))
        
        total = query.count()
        
        skip = page * size
        db_routes = query.offset(skip).limit(size).all()
        
        routes = [RouteService._model_to_schema(route, db=db, include_service_days=True) for route in db_routes]
        return routes, total
    
    @staticmethod
    def _route_direction_model_to_schema(db_route_direction: RouteDirectionModel) -> RouteDirection:
        return RouteDirection(
            route_id=db_route_direction.route_id,
            direction_id=db_route_direction.direction_id,
            service_id=db_route_direction.service_id,
            headsign=db_route_direction.headsign
        )
    
    @staticmethod
    def get_route_directions(
        db: Session,
        route_id: str,
        direction_id: Optional[int] = None,
        service_ids: Optional[List[str]] = None,
    ) -> List[RouteDirection]:
        query = db.query(RouteDirectionModel).filter(RouteDirectionModel.route_id == route_id)
        
        if direction_id is not None:
            query = query.filter(RouteDirectionModel.direction_id == direction_id)
        
        if service_ids:
            query = query.filter(RouteDirectionModel.service_id.in_(service_ids))
        
        db_route_directions = query.all()
        return [RouteService._route_direction_model_to_schema(rd) for rd in db_route_directions]
    
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
    def get_route_shapes(
        db: Session,
        route_id: str,
        direction_id: Optional[int] = None
    ) -> List[RouteShape]:
        
        # Query route_shapes table directly
        query = db.query(RouteShapeModel).filter(RouteShapeModel.route_id == route_id)
        if direction_id is not None:
            query = query.filter(RouteShapeModel.direction_id == direction_id)
        
        route_shapes = query.all()
        if not route_shapes:
            return []
        
        shape_ids = [rs.shape_id for rs in route_shapes]
        
        # Get all shape points for these shape_ids, ordered by shape_id and sequence
        db_shapes = db.query(ShapeModel).filter(
            ShapeModel.id.in_(shape_ids)
        ).order_by(ShapeModel.id, ShapeModel.sequence).all()
        
        # Group shape points by shape_id
        shapes_dict: Dict[str, List[ShapePoint]] = {}
        for db_shape in db_shapes:
            if db_shape.id not in shapes_dict:
                shapes_dict[db_shape.id] = []
            shapes_dict[db_shape.id].append(
                RouteService._shape_point_model_to_schema(db_shape)
            )
        
        all_route_shapes = []
        for route_shape in route_shapes:
            points = shapes_dict.get(route_shape.shape_id, [])
            if points:
                all_route_shapes.append(RouteShape(
                    shape_id=route_shape.shape_id,
                    direction_id=route_shape.direction_id,
                    points=points
                ))
        
        # Sort by direction_id and shape_id
        all_route_shapes.sort(key=lambda x: (x.direction_id, x.shape_id))
        
        return all_route_shapes
    
    @staticmethod
    def get_route_stops(
        db: Session,
        route_id: str,
        direction_id: Optional[int] = None
    ) -> List[RouteStop]:
        query = db.query(
            RouteStopModel,
            StopModel.name,
            StopModel.zone_id
        ).join(
            StopModel, RouteStopModel.stop_id == StopModel.id
        ).filter(RouteStopModel.route_id == route_id)
        
        if direction_id is not None:
            query = query.filter(RouteStopModel.direction_id == direction_id)
        
        results = query.order_by(RouteStopModel.direction_id, RouteStopModel.stop_sequence).all()
        
        if results:
            return [
                RouteStop(
                    route=RouteStopRouteInfo(
                        id=rs.route_id,
                        direction_id=rs.direction_id
                    ),
                    stop=RouteStopStopInfo(
                        id=rs.stop_id,
                        name=stop_name,
                        zone_id=zone_id
                    ),
                    sequence=rs.stop_sequence
                )
                for rs, stop_name, zone_id in results
            ]
        
        # Fallback: derive from trip_stops if route_stops table is empty
        # Get trips for this route
        trip_query = db.query(TripModel).filter(TripModel.route_id == route_id)
        if direction_id is not None:
            trip_query = trip_query.filter(TripModel.direction_id == direction_id)
        
        trips = trip_query.all()
        
        if not trips:
            return []
        
        trip_ids = [trip.trip_id for trip in trips]
        
        # Get unique stops with their sequences from trip_stops
        # Group by direction_id, stop_id and take the minimum sequence
        from sqlalchemy import func
        
        trip_stops_query = db.query(
            TripModel.direction_id,
            TripStopModel.stop_id,
            func.min(TripStopModel.sequence).label('min_sequence'),
            StopModel.name,
            StopModel.zone_id
        ).join(
            TripStopModel, TripModel.trip_id == TripStopModel.trip_id
        ).join(
            StopModel, TripStopModel.stop_id == StopModel.id
        ).filter(
            TripModel.trip_id.in_(trip_ids)
        ).group_by(
            TripModel.direction_id,
            TripStopModel.stop_id,
            StopModel.name,
            StopModel.zone_id
        )
        
        if direction_id is not None:
            trip_stops_query = trip_stops_query.filter(TripModel.direction_id == direction_id)
        
        trip_stops_results = trip_stops_query.order_by(
            TripModel.direction_id,
            func.min(TripStopModel.sequence)
        ).all()
        
        return [
            RouteStop(
                route=RouteStopRouteInfo(
                    id=route_id,
                    direction_id=dir_id
                ),
                stop=RouteStopStopInfo(
                    id=stop_id,
                    name=stop_name,
                    zone_id=zone_id
                ),
                sequence=int(min_sequence)
            )
            for dir_id, stop_id, min_sequence, stop_name, zone_id in trip_stops_results
        ]