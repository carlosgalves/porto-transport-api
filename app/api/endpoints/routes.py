from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.schemas.route import Route, RouteResponse, RouteStop, RouteStopsGroupedResponse, RouteDirectionStops, RouteStopItem
from app.api.schemas.shape import RouteShape
from app.api.schemas.response import SingleResponse, ListResponse, SimpleListResponse
from app.api.utils.pagination import create_paginated_response
from app.api.utils.response_builder import create_single_response, create_list_response, create_simple_list_response, build_route_links
from app.services.route_service import RouteService
from collections import defaultdict
from datetime import datetime

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("/", response_model=RouteResponse)
def get_routes(
    request: Request,
    service_id: Optional[str] = Query(None, description="Filter routes by comma-separated service IDs."),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    size: int = Query(100, ge=1, le=100, description="Page size (1-100)"),
    db: Session = Depends(get_db)
):
    """
    Get all routes.
    """
    service_ids = None
    if service_id:
        service_ids = [sid.strip() for sid in service_id.split(",") if sid.strip()]
    
    routes, total = RouteService.get_routes(
        db=db,
        service_ids=service_ids,
        page=page,
        size=size
    )
    
    return create_paginated_response(request, routes, total, page, size, RouteResponse)


@router.get("/{route_id}", response_model=SingleResponse[Route])
def get_route_by_id(
    request: Request,
    route_id: str,
    service_id: Optional[str] = Query(None, description="Filter directions by comma-separated service IDs"),
    db: Session = Depends(get_db)
):
    """
    Get a specific route by it's ID.
    """
    service_ids = None
    if service_id:
        service_ids = [sid.strip() for sid in service_id.split(",") if sid.strip()]
    
    route = RouteService.get_route_by_id(db=db, route_id=route_id, service_ids=service_ids)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    related_links = build_route_links(request, route_id)
    return create_single_response(route, request, related_links)


@router.get("/{route_id}/shapes", response_model=SimpleListResponse[RouteShape])
def get_route_shapes(
    request: Request,
    route_id: str,
    direction_id: Optional[int] = Query(None, description="Filter shapes by direction_id"),
    db: Session = Depends(get_db)
):
    """
    Get all shapes/stop points for a specific route.
    """
    route = RouteService.get_route_by_id(db=db, route_id=route_id, include_directions=False, service_ids=None)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    shapes = RouteService.get_route_shapes(
        db=db,
        route_id=route_id,
        direction_id=direction_id
    )
    
    return create_simple_list_response(shapes, request)


@router.get("/{route_id}/stops", response_model=RouteStopsGroupedResponse)
def get_route_stops(
    request: Request,
    route_id: str,
    direction_id: Optional[int] = Query(None, description="Filter stops by direction_id"),
    db: Session = Depends(get_db)
):
    """
    Get all stops for a specific route, grouped by direction_id.
    """
    route = RouteService.get_route_by_id(db=db, route_id=route_id, include_directions=False, service_ids=None)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    stops = RouteService.get_route_stops(
        db=db,
        route_id=route_id,
        direction_id=direction_id
    )
    
    # Group stops by direction_id
    stops_by_direction = defaultdict(list)
    
    for stop in stops:
        dir_id = stop.route.direction_id
        stops_by_direction[dir_id].append(
            RouteStopItem(
                stop=stop.stop,
                sequence=stop.sequence
            )
        )
    
    # Build direction groups, sorted by direction_id and stops by sequence
    direction_groups = [
        RouteDirectionStops(
            direction_id=dir_id,
            stops=sorted(stops_list, key=lambda s: s.sequence)
        )
        for dir_id, stops_list in sorted(stops_by_direction.items())
    ]
    
    from app.api.schemas.route import RouteStopsGroupedData
    
    return RouteStopsGroupedResponse(
        data=RouteStopsGroupedData(
            route_id=route_id,
            directions=direction_groups
        ),
        timestamp=datetime.utcnow()
    )