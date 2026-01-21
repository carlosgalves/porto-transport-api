from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List, Dict, Any
from datetime import datetime

T = TypeVar('T')


class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None)
    message: str = Field(...)
    code: Optional[str] = Field(None)


class ErrorResponse(BaseModel):
    error: bool = Field(True)
    message: str = Field(...)
    status_code: int = Field(...)
    details: Optional[List[ErrorDetail]] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(None)


class ResourceLinks(BaseModel):
    self: Optional[str] = Field(None)
    related: Optional[Dict[str, str]] = Field(None)


class SingleResponse(BaseModel, Generic[T]):
    data: T = Field(..., description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    links: Optional[ResourceLinks] = Field(None)


class ListResponse(BaseModel, Generic[T]):
    data: List[T] = Field(..., description="List of items")
    count: int = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SimpleListResponse(BaseModel, Generic[T]):
    data: List[T] = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)