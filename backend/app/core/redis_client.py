import json
import logging
from typing import Any

import redis

from app.core.config import settings


logger = logging.getLogger(__name__)

# Single client instance reused across all requests
_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def cache_get_json(key: str) -> Any | None:
    try:
        raw = get_redis_client().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except redis.exceptions.ConnectionError as exc:
        logger.warning("Redis unavailable (get %s): %s", key, exc)
        return None
    except Exception:
        logger.exception("Redis get failed for key %s", key)
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    ttl = ttl_seconds or settings.redis_cache_ttl_seconds
    try:
        get_redis_client().setex(key, ttl, json.dumps(value))
    except redis.exceptions.ConnectionError as exc:
        logger.warning("Redis unavailable (set %s): %s", key, exc)
    except Exception:
        logger.exception("Redis set failed for key %s", key)
