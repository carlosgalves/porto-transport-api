from pydantic import BaseModel, Field
from typing import List
from app.api.schemas.shared import Coordinates
from app.api.schemas.pagination import PaginatedResponse


class ShapePoint(BaseModel):
    sequence: int = Field(...)
    coordinates: Coordinates = Field(...)
    
    class Config:
        from_attributes = True


class TripShapesResponse(BaseModel):
    trip_id: str = Field(...)
    shape_id: str = Field(...)
    points: List[ShapePoint] = Field(...)


class RouteShape(BaseModel):
    shape_id: str = Field(...)
    direction_id: int = Field(...)
    points: List[ShapePoint] = Field(...)


class RouteShapesResponse(BaseModel):
    items: List[RouteShape] = Field(default_factory=list)