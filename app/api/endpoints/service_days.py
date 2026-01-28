from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.api.schemas.service_day import ServiceDay
from app.api.schemas.response import SimpleListResponse, SingleResponse
from app.api.utils.response_builder import create_simple_list_response, create_single_response
from app.services.service_day_service import ServiceDayService

router = APIRouter(prefix="/service-days", tags=["Service Days"])


@router.get("/", response_model=SimpleListResponse[ServiceDay])
def get_service_days(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all service days.
    """
    service_days = ServiceDayService.get_service_days(db=db)
    return create_simple_list_response(service_days, request)




@router.get("/{id}", response_model=SingleResponse[ServiceDay])
def get_service_day_by_id(
    request: Request,
    id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get a specific service day by its service_id or service_type.
    """
    service_day = ServiceDayService.get_service_day_by_id_or_type(db=db, identifier=id)
    if service_day is None:
        raise HTTPException(status_code=404, detail="Service day not found")
    
    return create_single_response(service_day, request)