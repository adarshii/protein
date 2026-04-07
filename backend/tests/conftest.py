"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.dependencies import rate_limiter


async def _noop_rate_limiter() -> None:
    """No-op override for the rate-limiter dependency used in tests."""
    return


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[rate_limiter] = _noop_rate_limiter
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(rate_limiter, None)


@pytest.fixture
def sample_dna_sequence():
    return "ATGCGATCGATCGATCGTAA"


@pytest.fixture
def sample_protein_sequence():
    return "MKALIVLGLVSSYGVQPHNGSRQT"


@pytest.fixture
def sample_smiles():
    return "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis
