from pydantic import BaseModel, Field


class RouteDirection(BaseModel):
    route_id: str = Field(...)
    direction_id: int = Field(...)
    service_id: str = Field(...)
    headsign: str = Field(...)
    
    class Config:
        from_attributes = True