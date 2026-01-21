from pydantic import BaseModel, Field
from typing import List

from app.api.schemas.pagination import PaginatedResponse


class TripInfo(BaseModel):
    id: str = Field(...)
    route_id: str = Field(...)
    direction_id: int = Field(...)
    service_id: str = Field(...)
    number: str = Field(...)


class Trip(BaseModel):
    trip: TripInfo = Field(...)
    headsign: str = Field(...)
    wheelchair_accessible: bool = Field(...)
    
    class Config:
        from_attributes = True


class TripResponse(PaginatedResponse[Trip]): pass


class TripStopStopInfo(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    zone_id: str = Field(...)


class TripStop(BaseModel):
    trip_id: str = Field(...)
    stop: TripStopStopInfo = Field(...)
    sequence: int = Field(...)
    
    class Config:
        from_attributes = True

