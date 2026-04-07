"""Custom exception types and global exception handlers."""

from __future__ import annotations

import traceback
from typing import Any, Dict

import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class BioChemException(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class SequenceValidationError(BioChemException):
    """Raised when a biological sequence fails validation."""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class MoleculeValidationError(BioChemException):
    """Raised when a chemical structure (SMILES/InChI) fails validation."""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


class ExternalAPIError(BioChemException):
    """Raised when an upstream API call fails."""

    def __init__(self, service: str, message: str, detail: Any = None) -> None:
        super().__init__(
            f"External API error from {service}: {message}",
            status.HTTP_502_BAD_GATEWAY,
            detail,
        )


class ResourceNotFoundError(BioChemException):
    """Raised when a requested resource cannot be found."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            f"{resource} '{identifier}' not found.",
            status.HTTP_404_NOT_FOUND,
        )


# ---------------------------------------------------------------------------
# Error response builder
# ---------------------------------------------------------------------------


def _error_response(
    status_code: int,
    error_type: str,
    message: str,
    detail: Any = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "type": error_type,
            "message": message,
            "detail": detail,
        },
        "status_code": status_code,
    }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI/Starlette HTTP exceptions."""
    logger.warning(
        "http_exception",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_response(
            exc.status_code,
            "HTTPException",
            str(exc.detail),
        ),
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic v2 validation errors."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "ValidationError",
            "Request payload validation failed.",
            exc.errors(),
        ),
    )


async def biochem_exception_handler(
    request: Request, exc: BioChemException
) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.warning(
        "biochem_exception",
        path=request.url.path,
        message=exc.message,
        status_code=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_response(
            exc.status_code,
            type(exc).__name__,
            exc.message,
            exc.detail,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        exc_type=type(exc).__name__,
        traceback=traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "InternalServerError",
            "An unexpected error occurred. Please try again later.",
        ),
    )
