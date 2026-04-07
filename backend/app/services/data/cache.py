"""Redis cache service with safe fallback behavior."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class CacheService:
    """Async cache wrapper backed by Redis."""

    def __init__(self, url: str, default_ttl: int = 3600) -> None:
        self.url = url
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def ping(self) -> bool:
        client = await self._get_client()
        return bool(await client.ping())

    async def get(self, key: str) -> Any:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_get_failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        try:
            client = await self._get_client()
            payload = json.dumps(value, default=str)
            await client.set(key, payload, ex=ttl or self.default_ttl)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_set_failed", key=key, error=str(exc))
            return False

    async def delete(self, key: str) -> int:
        try:
            client = await self._get_client()
            return int(await client.delete(key))
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_delete_failed", key=key, error=str(exc))
            return 0

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


cache_service = CacheService(
    url=settings.REDIS_URL,
    default_ttl=settings.DEFAULT_CACHE_TTL,
)


def cache_response(
    key_builder: Callable[P, str],
    ttl: int | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Cache async function output using Redis by computed key."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = key_builder(*args, **kwargs)
            cached = await cache_service.get(key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            await cache_service.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator

