"""Application entry point and FastAPI app factory."""

from __future__ import annotations

import time
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.exception_handlers import (
    BioChemException,
    biochem_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.utils.logger import configure_logging
from app.api import health, bioinformatics, chemoinformatics, ml_inference, genomics

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
logger = structlog.get_logger(__name__)
STARTUP_MAX_RETRIES = 5
STARTUP_RETRY_MAX_SLEEP_SECONDS = 10

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events."""
    logger.info("startup", version=settings.APP_VERSION)

    # Database
    from app.services.data.db import create_tables
    for attempt in range(1, STARTUP_MAX_RETRIES + 1):
        try:
            await create_tables()
            logger.info("database_ready", attempt=attempt)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("database_unavailable", attempt=attempt, error=str(exc))
            if attempt < STARTUP_MAX_RETRIES:
                await asyncio.sleep(min(2 * attempt, STARTUP_RETRY_MAX_SLEEP_SECONDS))

    # Redis
    from app.services.data.cache import cache_service
    for attempt in range(1, STARTUP_MAX_RETRIES + 1):
        try:
            await cache_service.ping()
            logger.info("redis_ready", attempt=attempt)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_unavailable", attempt=attempt, error=str(exc))
            if attempt < STARTUP_MAX_RETRIES:
                await asyncio.sleep(min(2 * attempt, STARTUP_RETRY_MAX_SLEEP_SECONDS))

    yield

    logger.info("shutdown")
    try:
        from app.services.data.cache import cache_service
        await cache_service.close()
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # ── Prometheus middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )
        return response

    # ── Request logging middleware ────────────────────────────────────────
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response

    # ── Exception handlers ────────────────────────────────────────────────
    from fastapi import HTTPException
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(BioChemException, biochem_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(health.router, tags=["Health"])
    app.include_router(
        bioinformatics.router, prefix="/api/bio", tags=["Bioinformatics"]
    )
    app.include_router(
        chemoinformatics.router, prefix="/api/chem", tags=["Chemoinformatics"]
    )
    app.include_router(
        ml_inference.router, prefix="/api/ml", tags=["ML Inference"]
    )
    app.include_router(
        genomics.router, prefix="/api/genomics", tags=["Genomics"]
    )

    # ── Metrics endpoint ──────────────────────────────────────────────────
    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
