from __future__ import annotations

from typing import Optional

from app.core.config import settings

_redis_client: Optional[object] = None


async def get_redis() -> "redis.asyncio.Redis":
    global _redis_client
    if _redis_client is None:
        if not settings.REDIS_URL:
            raise RuntimeError("REDIS_URL must be set. Redis is required for the API.")
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None