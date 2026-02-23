import json
import logging
from typing import Any

import redis

from app.core.config import settings


logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def cache_get_json(key: str) -> Any | None:
    try:
        raw = get_redis_client().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.exception("Redis get failed", extra={"key": key})
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds or settings.redis_cache_ttl_seconds
    try:
        get_redis_client().setex(key, ttl, json.dumps(value))
    except Exception:
        logger.exception("Redis set failed", extra={"key": key})
