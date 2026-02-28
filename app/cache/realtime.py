import json
from typing import List, Optional, Tuple

from app.api.schemas.arrival import RealtimeArrival
from app.core.config import settings
from app.core.redis import get_redis

CACHE_KEY_PREFIX = "realtime:"


def _serialize(items: List[RealtimeArrival]) -> str:
    return json.dumps([item.model_dump(mode="json") for item in items])


def _deserialize(data: str) -> List[RealtimeArrival]:
    raw = json.loads(data)
    return [RealtimeArrival.model_validate(item) for item in raw]


async def get_realtime_arrivals_cached(stop_id: str) -> Optional[Tuple[List[RealtimeArrival], int]]:
    redis = await get_redis()
    key = f"{CACHE_KEY_PREFIX}{stop_id}"
    try:
        data = await redis.get(key)
        if data is None:
            return None
        items = _deserialize(data)
        return (items, len(items))
    except Exception:
        return None


async def set_realtime_arrivals_cached(stop_id: str, items: List[RealtimeArrival]) -> None:
    redis = await get_redis()
    key = f"{CACHE_KEY_PREFIX}{stop_id}"
    ttl = settings.REDIS_REALTIME_TTL
    data = _serialize(items)
    await redis.setex(key, ttl, data)