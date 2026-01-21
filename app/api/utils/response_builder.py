from fastapi import Request
from typing import List, Optional, Dict, TypeVar, Type
from datetime import datetime
from app.api.schemas.response import SingleResponse, ListResponse, ResourceLinks
from app.api.schemas.pagination import PaginatedResponse

T = TypeVar('T')


def create_single_response(
    data: T,
    request: Optional[Request] = None,
    related_links: Optional[Dict[str, str]] = None
) -> SingleResponse[T]:
    links = None
    if request or related_links:
        self_link = str(request.url) if request else None
        if related_links is not None:
            links = ResourceLinks(self=self_link, related=related_links)
        else:
            links = ResourceLinks(self=self_link)
    
    return SingleResponse(
        data=data,
        timestamp=datetime.utcnow(),
        links=links
    )


def create_list_response(
    items: List[T],
    request: Optional[Request] = None
) -> ListResponse[T]:
    return ListResponse(
        data=items,
        count=len(items),
        timestamp=datetime.utcnow()
    )


def create_simple_list_response(
    items: List[T],
    request: Optional[Request] = None
) -> "SimpleListResponse[T]":
    from app.api.schemas.response import SimpleListResponse
    return SimpleListResponse(
        data=items,
        timestamp=datetime.utcnow()
    )


def build_route_links(request: Request, route_id: str) -> Dict[str, str]:
    base_url = str(request.base_url).rstrip('/')
    return {
        "shapes": f"{base_url}/api/v1/stcp/routes/{route_id}/shapes",
        "stops": f"{base_url}/api/v1/stcp/routes/{route_id}/stops"
    }


def build_trip_links(request: Request, trip_id: str) -> Dict[str, str]:
    base_url = str(request.base_url).rstrip('/')
    return {
        "shapes": f"{base_url}/api/v1/stcp/trips/{trip_id}/shapes",
        "stops": f"{base_url}/api/v1/stcp/trips/{trip_id}/stops"
    }


def build_stop_links(request: Request, stop_id: str) -> Dict[str, str]:
    base_url = str(request.base_url).rstrip('/')
    return {
        "scheduled_arrivals": f"{base_url}/api/v1/stcp/stops/{stop_id}/scheduled",
        "realtime_arrivals": f"{base_url}/api/v1/stcp/stops/{stop_id}/realtime"
    }
