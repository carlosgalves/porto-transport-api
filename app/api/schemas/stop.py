from pydantic import BaseModel, Field
from app.api.schemas.shared import Coordinates
from app.api.schemas.pagination import PaginatedResponse


class Stop(BaseModel):
    id: str = Field(...)
    name: str = Field()
    coordinates: Coordinates = Field()
    zone_id: str = Field(...)


class StopResponse(PaginatedResponse[Stop]): pass