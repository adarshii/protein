"""Health check endpoints."""

from __future__ import annotations

import time
from typing import Any, Dict

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

_START_TIME = time.time()


def _uptime() -> float:
    return round(time.time() - _START_TIME, 2)


@router.get("/health", summary="Basic liveness probe")
async def health() -> Dict[str, Any]:
    """Return application liveness status."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "uptime_seconds": _uptime(),
        "timestamp": time.time(),
    }


@router.get("/health/db", summary="Database connectivity probe")
async def health_db() -> Dict[str, Any]:
    """Check PostgreSQL connectivity."""
    try:
        from app.services.data.db import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("db_health_check_failed", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unreachable"},
        )


@router.get("/health/redis", summary="Redis connectivity probe")
async def health_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        from app.services.data.cache import cache_service
        await cache_service.ping()
        return {"status": "ok", "redis": "reachable"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_health_check_failed", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "redis": "unreachable"},
        )


@router.get("/health/ready", summary="Readiness probe")
async def health_ready() -> Dict[str, Any]:
    """Kubernetes-style readiness probe — checks all dependencies."""
    checks: Dict[str, str] = {}
    overall = "ok"

    # DB
    try:
        from app.services.data.db import engine
        import sqlalchemy
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"
        overall = "degraded"

    # Redis
    try:
        from app.services.data.cache import cache_service
        await cache_service.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"
        overall = "degraded"

    http_status = (
        status.HTTP_200_OK if overall == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall,
            "checks": checks,
            "version": settings.APP_VERSION,
            "timestamp": time.time(),
        },
    )
