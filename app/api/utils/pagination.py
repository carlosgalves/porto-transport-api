from fastapi import Request, Query
from typing import Optional, TypeVar, List, Type
from urllib.parse import urlencode
from datetime import datetime
from app.api.schemas.pagination import PageInfo, Links, PaginatedResponse

T = TypeVar('T')


def get_pagination_params(
    page: int = Query(0, ge=0),
    size: int = Query(100, ge=1, le=100)
) -> tuple[int, int]:
    return page, size


def build_pagination_url(request: Request, page: Optional[int] = None) -> str:
    
    query_params = dict(request.query_params)
    
    if page is not None:
        query_params["page"] = str(page)
    
    base_url = str(request.url).split("?")[0]
    if query_params:
        return f"{base_url}?{urlencode(query_params, doseq=True)}"
    return base_url


def create_pagination_info(
    request: Request,
    total: int,
    page: int,
    size: int
) -> tuple[PageInfo, Links, datetime]:
    total_pages = (total + size - 1) // size if total > 0 else 0
    
    # navigation links
    self_url = build_pagination_url(request, page=page)
    first_url = build_pagination_url(request, page=0)
    last_page = max(0, total_pages - 1) if total_pages > 0 else 0
    last_url = build_pagination_url(request, page=last_page)
    next_url = build_pagination_url(request, page=page + 1) if page < total_pages - 1 else None
    prev_url = build_pagination_url(request, page=page - 1) if page > 0 else None
    
    page_info = PageInfo(
        size=size,
        totalElements=total,
        totalPages=total_pages,
        number=page
    )
    
    links = Links(
        self=self_url,
        first=first_url,
        next=next_url,
        prev=prev_url,
        last=last_url
    )
    
    timestamp = datetime.utcnow()
    
    return page_info, links, timestamp


def create_paginated_response(
    request: Request,
    items: List[T],
    total: int,
    page: int,
    size: int,
    response_class: Type[PaginatedResponse[T]]
) -> PaginatedResponse[T]:
    page_info, links, timestamp = create_pagination_info(request, total, page, size)
    
    return response_class(
        data=items,
        page=page_info,
        links=links,
        timestamp=timestamp
    )