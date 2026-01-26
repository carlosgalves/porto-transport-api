from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.api.schemas.stop import Stop, StopResponse
from app.api.schemas.arrival import ScheduledArrival, ScheduledArrivalResponse, RealtimeArrival, RealtimeArrivalsResponse
from app.api.schemas.response import SingleResponse
from app.api.utils.pagination import create_paginated_response
from app.api.utils.response_builder import create_single_response, build_stop_links
from app.services.stop_service import StopService


router = APIRouter(prefix="/stops", tags=["Stops"])

@router.get("/", response_model=StopResponse)
def get_stops(
    request: Request,
    zone_id: Optional[str] = Query(None, description="Filter stops by zone_id"),
    page: int = Query(0, ge=0, description="Page number"),
    size: Optional[int] = Query(None, ge=1, le=100, description="Page size (1-100). If not provided, returns all stops."),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all stops.
    If size is not provided, returns all stops without pagination.
    """
    stops, total = StopService.get_stops(db=db, zone_id=zone_id, page=page, size=size)
    
    effective_size = size if size is not None else total
    effective_page = 0 if size is None else page
    
    return create_paginated_response(request, stops, total, effective_page, effective_size, StopResponse)


@router.get("/{stop_id}", response_model=SingleResponse[Stop])
def get_stop_by_id(
    request: Request,
    stop_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get a specific stop by it's ID.
    """
    stop = StopService.get_stop_by_id(db=db, stop_id=stop_id)
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    related_links = build_stop_links(request, stop_id)
    return create_single_response(stop, request, related_links)


@router.get("/{stop_id}/scheduled", response_model=ScheduledArrivalResponse)
def get_scheduled_arrivals(
    request: Request,
    stop_id: str,
    route_id: Optional[str] = Query(None, description="Filter arrivals by route_id"),
    service_id: Optional[str] = Query(None, description="Filter arrivals by service_id (service day)"),
    page: int = Query(0, ge=0, description="Page number"),
    size: int = Query(100, ge=1, le=100, description="Page size (1-100)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get scheduled arrivals for a specific stop.
    Returns all scheduled arrivals ordered by arrival time.
    
    Optionally filter by route_id and/or service_id.
    """
    stop = StopService.get_stop_by_id(db=db, stop_id=stop_id)
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    arrivals, total = StopService.get_scheduled_arrivals(
        db=db,
        stop_id=stop_id,
        route_id=route_id,
        service_id=service_id,
        page=page,
        size=size
    )
    
    return create_paginated_response(request, arrivals, total, page, size, ScheduledArrivalResponse)


@router.get("/{stop_id}/realtime", response_model=SingleResponse[RealtimeArrivalsResponse])
async def get_realtime_arrivals(
    request: Request,
    stop_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get real-time arrivals for a specific stop.
    """
    response = await StopService.get_realtime_arrivals_response(db=db, stop_id=stop_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    return create_single_response(response, request)