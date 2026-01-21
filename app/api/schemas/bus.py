from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.api.schemas.pagination import PaginatedResponse


class BusTrip(BaseModel):
    trip_id: str = Field(...)
    service_id: str = Field(...)
    trip_number: Optional[str] = Field(None)
    headsign: str = Field(...)
    wheelchair_accessible: bool = Field(...)


class BusRoute(BaseModel):
    route_id: str = Field(...)
    headsign: str = Field(...)
    direction: str = Field(...)


class BusCoordinates(BaseModel):
    lat: float = Field(...)
    lon: float = Field(...)
    heading: Optional[float] = Field(None)


class Bus(BaseModel):
    vehicle_id: str = Field(...)
    trip: Optional[BusTrip] = Field(None)
    route: Optional[BusRoute] = Field(None)
    coordinates: BusCoordinates = Field(...)
    speed: Optional[float] = Field(None)
    last_updated: datetime = Field(...)
    
    class Config:
        from_attributes = True


class BusResponse(PaginatedResponse[Bus]): pass
