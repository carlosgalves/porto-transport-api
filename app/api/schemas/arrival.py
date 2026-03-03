from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import time, datetime
from app.api.schemas.pagination import PaginatedResponse


class TripInfo(BaseModel):
    id: str = Field(...)
    route_id: str = Field(...)
    direction_id: int = Field(...)
    service_id: str = Field(...)
    number: str = Field(...)
    headsign: str = Field(...)
    raw_trip_id: Optional[str] = Field(None)


class StopInfo(BaseModel):
    id: str = Field(...)
    sequence: Optional[int] = Field(None)


class ScheduledArrival(BaseModel):
    trip: TripInfo = Field(...)
    stop: StopInfo = Field(...)
    # all = false => use ISO 8601 datetime
    # all = true => use time only
    arrival_time: Union[datetime, time] = Field(...)
    departure_time: Union[datetime, time] = Field(...)


class RealtimeArrival(BaseModel):
    vehicle_id: str = Field(...)
    trip: TripInfo = Field(...)
    stop: StopInfo = Field(...)
    realtime_arrival_time: Optional[datetime] = Field(None, description="ISO 8601 datetime")
    scheduled_arrival_time: Optional[datetime] = Field(None, description="ISO 8601 datetime")
    arrival_minutes: Optional[float] = Field(None)
    delay_minutes: Optional[float] = Field(None)
    status: Optional[str] = Field(None)
    last_updated: datetime = Field(...)

    class Config:
        from_attributes = True


class RealtimeArrivalsResponse(PaginatedResponse[RealtimeArrival]): pass

class ScheduledArrivalResponse(PaginatedResponse[ScheduledArrival]): pass