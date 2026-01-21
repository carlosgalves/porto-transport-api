from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    latitude: float = Field()
    longitude: float = Field()