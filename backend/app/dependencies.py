"""FastAPI dependency injection providers."""

from __future__ import annotations

import time
from typing import AsyncGenerator, Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.data.db import AsyncSessionLocal

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, closing it when done."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------


async def get_redis():  # type: ignore[return]
    """Yield a Redis connection from the application-level pool."""
    from app.services.data.cache import cache_service

    yield cache_service


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    """Return the current user payload if a valid token is present; else None."""
    if token is None:
        return None
    return _decode_token(token)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """Require a valid JWT token; raise 401 if missing or invalid."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(token)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

# In-memory store keyed by (ip, window_start). Production → use Redis.
_rate_limit_store: dict[str, tuple[int, float]] = {}


async def rate_limiter(request) -> None:  # type: ignore[type-arg]
    """Simple sliding-window rate limiter based on client IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_REQUESTS

    count, window_start = _rate_limit_store.get(client_ip, (0, now))
    if now - window_start > window:
        count, window_start = 0, now

    count += 1
    _rate_limit_store[client_ip] = (count, window_start)

    if count > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {max_requests} requests per {window}s.",
        )


# ---------------------------------------------------------------------------
# Cache helper dependency
# ---------------------------------------------------------------------------


class CacheDependency:
    """Dependency that wraps the cache service for use in route handlers."""

    async def __call__(self):
        from app.services.data.cache import cache_service

        return cache_service


get_cache = CacheDependency()
