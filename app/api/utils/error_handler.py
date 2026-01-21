from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import List
from app.api.schemas.response import ErrorResponse, ErrorDetail
import uuid


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error_response = ErrorResponse(
        error=True,
        message=exc.detail if hasattr(exc, 'detail') else "An error occurred",
        status_code=exc.status_code,
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(ErrorDetail(
            field=field if field else None,
            message=error.get("msg", "Validation error"),
            code=error.get("type")
        ))
    
    error_response = ErrorResponse(
        error=True,
        message="Validation error: Invalid request parameters",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    error_response = ErrorResponse(
        error=True,
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True)
    )