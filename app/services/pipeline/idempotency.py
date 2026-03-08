"""C1: Idempotency for pipeline run creation. Redis when REDIS_URL set (multi-instance); else in-memory."""
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_CACHE: dict = {}
_LOCK = threading.Lock()
_TTL_SECONDS = 120
_redis_client = None
_redis_available = None


def _get_redis():
    """Lazy init Redis client from REDIS_URL. Returns None if not configured or connection fails."""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        from flask import current_app
        url = current_app.config.get('REDIS_URL', '') or ''
        if not url:
            _redis_available = False
            return None
        import redis
        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
        _redis_available = True
        return _redis_client
    except Exception as e:
        logger.warning("Redis idempotency unavailable: %s", e)
        _redis_available = False
        return None


def _get_ttl():
    try:
        from flask import current_app
        return int(current_app.config.get('IDEMPOTENCY_TTL_SECONDS', _TTL_SECONDS))
    except Exception:
        return _TTL_SECONDS


def _redis_key(script_id: str, idempotency_key: str) -> str:
    return f"idempotency:pipeline:{script_id}:{idempotency_key}"


def _prune_memory():
    now = time.time()
    ttl = _get_ttl()
    to_del = [k for k, (_, ts) in _CACHE.items() if now - ts > ttl]
    for k in to_del:
        del _CACHE[k]


def get_cached_run_for_key(script_id: str, idempotency_key: str) -> Optional[str]:
    """Return run_id if this (script_id, idempotency_key) was used recently (Redis or memory)."""
    if not idempotency_key:
        return None
    r = _get_redis()
    if r is not None:
        try:
            key = _redis_key(script_id, idempotency_key)
            run_id = r.get(key)
            return run_id if run_id else None
        except Exception as e:
            logger.warning("Redis get failed, fallback to memory: %s", e)
    with _LOCK:
        _prune_memory()
        entry = _CACHE.get((script_id, idempotency_key))
        if not entry:
            return None
        run_id, ts = entry
        if time.time() - ts > _get_ttl():
            del _CACHE[(script_id, idempotency_key)]
            return None
        return run_id


def set_cached_run_for_key(script_id: str, idempotency_key: str, run_id: str) -> None:
    """Store run_id for this (script_id, idempotency_key) with TTL."""
    if not idempotency_key:
        return
    ttl = _get_ttl()
    r = _get_redis()
    if r is not None:
        try:
            key = _redis_key(script_id, idempotency_key)
            r.setex(key, ttl, run_id)
            return
        except Exception as e:
            logger.warning("Redis set failed, fallback to memory: %s", e)
    with _LOCK:
        _prune_memory()
        _CACHE[(script_id, idempotency_key)] = (run_id, time.time())
