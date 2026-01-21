from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.api.schemas.pagination import PaginatedResponse


class RouteDirectionItem(BaseModel):
    headsign: str = Field(...)
    direction_id: int = Field(...)
    service_days: List[str] = Field(...)


class Route(BaseModel):
    id: str = Field(...)
    short_name: str = Field(...)
    long_name: str = Field(...)
    type: int = Field(...)
    route_color: str = Field(...)
    route_text_color: str = Field(...)
    service_days: List[str] = Field(default_factory=list)
    directions: Optional[List[RouteDirectionItem]] = Field(None)
    
    class Config:
        from_attributes = True


class RouteResponse(PaginatedResponse[Route]): pass


class RouteStopRouteInfo(BaseModel):
    id: str = Field(...)
    direction_id: int = Field(...)


class RouteStopStopInfo(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    zone_id: str = Field(...)


class RouteStop(BaseModel):
    route: RouteStopRouteInfo = Field(...)
    stop: RouteStopStopInfo = Field(...)
    sequence: int = Field(...)
    
    class Config:
        from_attributes = True


class RouteStopItem(BaseModel):
    stop: RouteStopStopInfo = Field(...)
    sequence: int = Field(...)


class RouteDirectionStops(BaseModel):
    direction_id: int = Field(...)
    stops: List[RouteStopItem] = Field(...)


class RouteStopsGroupedData(BaseModel):
    route_id: str = Field(...)
    directions: List[RouteDirectionStops] = Field(...)


class RouteStopsGroupedResponse(BaseModel):
    data: RouteStopsGroupedData = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)