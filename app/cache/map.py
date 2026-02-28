import json
from typing import List, Optional, Tuple

from app.api.schemas.stop import Stop
from app.api.schemas.route import Route
from app.core.config import settings
from app.core.redis import get_redis

CACHE_KEY_STOPS = "map:stops"
CACHE_KEY_STOPS_ZONE = "map:stops:zone:{zone_id}"
CACHE_KEY_ROUTES = "map:routes"
CACHE_KEY_ROUTES_SERVICE = "map:routes:service:{service_ids}"


def _stops_key(zone_id: Optional[str]) -> str:
    if zone_id:
        return CACHE_KEY_STOPS_ZONE.format(zone_id=zone_id)
    return CACHE_KEY_STOPS


def _routes_key(service_ids: Optional[List[str]]) -> str:
    if service_ids:
        sorted_ids = ",".join(sorted(service_ids))
        return CACHE_KEY_ROUTES_SERVICE.format(service_ids=sorted_ids)
    return CACHE_KEY_ROUTES


async def get_stops_cached(zone_id: Optional[str]) -> Optional[Tuple[List[Stop], int]]:
    redis = await get_redis()
    key = _stops_key(zone_id)
    try:
        data = await redis.get(key)
        if data is None:
            return None
        raw = json.loads(data)
        stops = [Stop.model_validate(item) for item in raw]
        return (stops, len(stops))
    except Exception:
        return None


async def set_stops_cached(zone_id: Optional[str], stops: List[Stop]) -> None:
    redis = await get_redis()
    key = _stops_key(zone_id)
    ttl = settings.REDIS_MAP_TTL
    data = json.dumps([s.model_dump(mode="json") for s in stops])
    await redis.setex(key, ttl, data)


async def get_routes_cached(service_ids: Optional[List[str]]) -> Optional[Tuple[List[Route], int]]:
    redis = await get_redis()
    key = _routes_key(service_ids)
    try:
        data = await redis.get(key)
        if data is None:
            return None
        raw = json.loads(data)
        routes = [Route.model_validate(item) for item in raw]
        return (routes, len(routes))
    except Exception:
        return None


async def set_routes_cached(service_ids: Optional[List[str]], routes: List[Route]) -> None:
    redis = await get_redis()
    key = _routes_key(service_ids)
    ttl = settings.REDIS_MAP_TTL
    data = json.dumps([r.model_dump(mode="json") for r in routes])
    await redis.setex(key, ttl, data)