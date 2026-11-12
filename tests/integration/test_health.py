"""Integration tests for the health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root_health_returns_200():
    """Test that the root /health endpoint returns HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_health_has_correct_fields():
    """Test that the root /health response contains expected fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["service"] == "NIFTY Options Pricing API"


@pytest.mark.asyncio
async def test_v1_health_returns_200():
    """Test that the /api/v1/health endpoint returns HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_v1_health_has_correct_fields():
    """Test that the /api/v1/health response contains expected fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["service"] == "NIFTY Options Pricing API"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_docs_endpoint_returns_200():
    """Test that the Swagger UI /docs endpoint returns HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc_endpoint_returns_200():
    """Test that the ReDoc /redoc endpoint returns HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/redoc")
    assert response.status_code == 200
