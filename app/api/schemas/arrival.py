from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import time, datetime
from app.api.schemas.pagination import PaginatedResponse


class TripInfo(BaseModel):
    id: str = Field(...)
    route_id: str = Field(...)
    direction_id: int = Field(...)
    service_id: str = Field(...)
    number: str = Field(...)
    headsign: str = Field(...)


class StopInfo(BaseModel):
    id: str = Field(...)
    sequence: int = Field(...)


class ScheduledArrival(BaseModel):
    trip: TripInfo = Field(...)
    stop: StopInfo = Field(...)
    arrival_time: time = Field(...)
    departure_time: time = Field(...)
    
    class Config:
        from_attributes = True


class RealtimeArrival(BaseModel):
    vehicle_id: str = Field(...)
    trip: TripInfo = Field(...)
    stop: StopInfo = Field(...)
    realtime_arrival_time: Optional[time] = Field(None)
    scheduled_arrival_time: Optional[time] = Field(None)
    arrival_minutes: Optional[float] = Field(None)
    delay_minutes: Optional[float] = Field(None)
    status: Optional[str] = Field(None)
    last_updated: datetime = Field(...)
    
    class Config:
        from_attributes = True


class RealtimeArrivalsResponse(PaginatedResponse[RealtimeArrival]): pass

class ScheduledArrivalResponse(PaginatedResponse[ScheduledArrival]): pass