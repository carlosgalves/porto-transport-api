from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.api.schemas.trip import Trip, TripResponse, TripStop
from app.api.schemas.shape import TripShapesResponse
from app.api.schemas.response import SimpleListResponse, SingleResponse
from app.api.utils.pagination import create_paginated_response
from app.api.utils.response_builder import create_simple_list_response, create_single_response, build_trip_links
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("/", response_model=TripResponse)
def get_trips(
    request: Request,
    route_id: Optional[str] = Query(None),
    service_id: Optional[str] = Query(None),
    direction_id: Optional[int] = Query(None, description="only works when route_id is provided"),
    wheelchair_accessible: Optional[int] = Query(None),
    page: int = Query(0, ge=0),
    size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get trips with optional filtering and pagination.
    """
    trips, total = TripService.get_trips(
        db=db,
        route_id=route_id,
        service_id=service_id,
        direction_id=direction_id if route_id else None,
        wheelchair_accessible=wheelchair_accessible,
        page=page,
        size=size
    )
    
    return create_paginated_response(request, trips, total, page, size, TripResponse)


@router.get("/{trip_id}", response_model=SingleResponse[Trip])
def get_trip_by_id(
    request: Request,
    trip_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get a specific trip by its id.
    """
    trip = TripService.get_trip_by_trip_id(db=db, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    related_links = build_trip_links(request, trip_id)
    return create_single_response(trip, request, related_links)
    

@router.get("/{trip_id}/shapes", response_model=SingleResponse[TripShapesResponse])
def get_trip_shapes(
    request: Request,
    trip_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all shape points for a specific trip by its id.
    Returns the shape id and an ordered list of shape points (coordinates) that define the trip's route.
    """
    shapes = TripService.get_trip_shapes(db=db, trip_id=trip_id)
    if shapes is None:
        raise HTTPException(status_code=404, detail="Trip shapes not found")
    
    return create_single_response(shapes, request)


@router.get("/{trip_id}/stops", response_model=SimpleListResponse[TripStop])
def get_trip_stops(
    request: Request,
    trip_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all stops for a specific trip by its id.
    """
    # Verify trip exists
    trip = TripService.get_trip_by_trip_id(db=db, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    stops = TripService.get_trip_stops(db=db, trip_id=trip_id)
    return create_simple_list_response(stops, request)