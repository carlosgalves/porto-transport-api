from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic, List
from datetime import datetime

T = TypeVar('T')


class PageInfo(BaseModel):
    size: int = Field(...)
    totalElements: int = Field(...)
    totalPages: int = Field(...)
    number: int = Field(...)


class Links(BaseModel):
    self: Optional[str] = Field(None)
    first: Optional[str] = Field(None)
    next: Optional[str] = Field(None)
    last: Optional[str] = Field(None)
    prev: Optional[str] = Field(None)


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T] = Field(...)
    page: PageInfo = Field(...)
    links: Links = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)