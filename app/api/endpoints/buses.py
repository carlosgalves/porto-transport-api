from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.api.schemas.bus import Bus, BusResponse
from app.api.schemas.response import SingleResponse
from app.api.utils.pagination import create_paginated_response
from app.api.utils.response_builder import create_single_response
from app.services.bus_service import BusService

router = APIRouter(prefix="/buses", tags=["Buses"])


@router.get("/", response_model=BusResponse)
def get_buses(
    request: Request,
    route_id: Optional[str] = Query(None, description="Filter buses by route_id"),
    direction_id: Optional[int] = Query(None, description="Filter buses by direction_id (only works when route_id is provided)"),
    page: int = Query(0, ge=0, description="Page number"),
    size: int = Query(100, ge=1, le=100, description="Page size (1-100)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all buses.
    """
    buses, total = BusService.get_buses(
        db=db,
        route_id=route_id,
        direction_id=direction_id if route_id else None,
        page=page,
        size=size
    )
    
    return create_paginated_response(request, buses, total, page, size, BusResponse)


@router.get("/{vehicle_id}", response_model=SingleResponse[Bus])
def get_bus_by_id(
    request: Request,
    vehicle_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get a specific bus by its vehicle_id.
    """
    bus = BusService.get_bus_by_id(db=db, vehicle_id=vehicle_id)
    if bus is None:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    return create_single_response(bus, request)