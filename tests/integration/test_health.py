"""Integration tests for health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Test root endpoint returns API info."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "QAUserSearch API"
    assert data["version"] == "0.1.0"
    assert data["docs_url"] == "/docs"


@pytest.mark.asyncio
async def test_liveness_endpoint(async_client: AsyncClient) -> None:
    """Test liveness probe returns alive status."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["alive"] is True


@pytest.mark.asyncio
async def test_health_endpoint_structure(async_client: AsyncClient) -> None:
    """Test health endpoint returns correct structure."""
    response = await async_client.get("/health")

    # May be 200 or 503 depending on database availability
    assert response.status_code in [200, 503]
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "checks" in data
    assert isinstance(data["checks"], list)


@pytest.mark.asyncio
async def test_readiness_endpoint(async_client: AsyncClient) -> None:
    """Test readiness probe returns ready status."""
    response = await async_client.get("/health/ready")

    # May be 200 or 503 depending on database availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ready" in data
    assert isinstance(data["ready"], bool)
