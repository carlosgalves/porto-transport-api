import json
from typing import List, Optional, Tuple, Dict, Any

from app.api.schemas.arrival import RealtimeArrival
from app.core.config import settings
from app.core.redis import get_redis

CACHE_KEY_PREFIX = "realtime:"
TRIP_INFO_KEY_PREFIX = "realtime:trip:"


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
    # Store trip_id and trip_number by raw_trip_id so bus response can use realtime trip info
    for item in items:
        if item.trip and item.trip.raw_trip_id:
            trip_key = f"{TRIP_INFO_KEY_PREFIX}{item.trip.raw_trip_id}"
            trip_value = json.dumps({"trip_id": item.trip.id, "trip_number": item.trip.number or ""})
            await redis.setex(trip_key, ttl, trip_value)


async def get_trip_info_by_raw_trip_id(raw_trip_id: str) -> Optional[Dict[str, Any]]:
    if not raw_trip_id:
        return None
    redis = await get_redis()
    key = f"{TRIP_INFO_KEY_PREFIX}{raw_trip_id}"
    try:
        data = await redis.get(key)
        if data is None:
            return None
        out = json.loads(data)
        return {"trip_id": out.get("trip_id"), "trip_number": out.get("trip_number") or None}
    except Exception:
        return None


async def get_trip_info_for_raw_trip_ids(raw_trip_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not raw_trip_ids:
        return {}
    redis = await get_redis()
    keys = [f"{TRIP_INFO_KEY_PREFIX}{rid}" for rid in raw_trip_ids]
    try:
        values = await redis.mget(keys)
        result: Dict[str, Dict[str, Any]] = {}
        for raw_trip_id, val in zip(raw_trip_ids, values or []):
            if val:
                try:
                    out = json.loads(val)
                    result[raw_trip_id] = {
                        "trip_id": out.get("trip_id"),
                        "trip_number": out.get("trip_number") or None,
                    }
                except Exception:
                    pass
        return result
    except Exception:
        return {}