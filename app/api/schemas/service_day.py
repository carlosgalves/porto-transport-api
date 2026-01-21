import json
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class ServiceDay(BaseModel):
    service_id: str = Field(...)
    service_name: str = Field(...,)
    service_type: Optional[int] = Field(None)
    day_map: List[int] = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)
    
    @field_validator('day_map', mode='before')
    @classmethod
    def parse_day_map(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    class Config:
        from_attributes = True