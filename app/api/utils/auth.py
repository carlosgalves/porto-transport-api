from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from app.core.config import settings


api_key_header = APIKeyHeader(
    name=settings.API_KEY_HEADER,
    description="API key for authentication. Can be provided via header or query parameter.",
    auto_error=False
)
api_key_query = APIKeyQuery(
    name="api_key",
    description="API key for authentication. Can be provided via header or query parameter.",
    auto_error=False
)


async def verify_api_key(
    api_key_header_value: str = Security(api_key_header),
    api_key_query_value: str = Security(api_key_query),
) -> str:
    if not settings.API_KEY:
        # If no API key is configured, allow all requests (for development)
        return "no_auth_configured"
    
    api_key = api_key_header_value or api_key_query_value
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide it via X-API-Key header or api_key query parameter.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
    
    return api_key