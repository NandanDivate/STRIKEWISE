"""Integration tests for the options API endpoints."""

from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def future_expiry_iso() -> str:
    ist = timezone(timedelta(hours=5, minutes=30))
    expiry = datetime.now(ist) + timedelta(days=14)
    return expiry.isoformat()


@pytest.mark.asyncio
async def test_estimate_endpoint_valid_ce(future_expiry_iso: str):
    """Test POST /api/v1/options/estimate with valid Call request."""
    payload = {
        "underlying_symbol": "NIFTY",
        "current_spot": 24500.0,
        "target_spot": 24850.0,
        "option_type": "CE",
        "strike_price": 24600.0,
        "entry_premium": 110.50,
        "quantity": 50,
        "expiry": future_expiry_iso,
        "expected_time_to_target_minutes": 180.0,
        "implied_volatility_percent": 13.5,
        "risk_free_rate_percent": 7.0,
        "dividend_yield_percent": 1.2,
        "iv_shift_points": 2.0,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/estimate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "Black-Scholes-Merton"
    assert data["target_spot"] == 24850.0
    assert data["base_estimated_premium"] > 0.0
    assert len(data["scenarios"]) == 3
    assert data["greeks"]["delta"] is not None
    assert data["gross_profit_per_unit"] is not None
    assert data["gross_pnl"] is not None
    assert data["time_decay_comparison"]["theoretical_decay"] is not None


@pytest.mark.asyncio
async def test_estimate_endpoint_valid_pe(future_expiry_iso: str):
    """Test POST /api/v1/options/estimate with valid Put request."""
    payload = {
        "underlying_symbol": "NIFTY",
        "current_spot": 24500.0,
        "target_spot": 24200.0,
        "option_type": "PE",
        "strike_price": 24500.0,
        "entry_premium": 125.0,
        "quantity": 25,
        "expiry": future_expiry_iso,
        "expected_time_to_target_minutes": 120.0,
        "implied_volatility_percent": 14.0,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/estimate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["base_estimated_premium"] > 0.0
    assert -1.0 <= data["greeks"]["delta"] <= 0.0


@pytest.mark.asyncio
async def test_estimate_endpoint_validation_error_returns_422():
    """Test that invalid request body returns HTTP 422 with validation errors."""
    payload = {
        "current_spot": -24500.0,  # Negative spot invalid
        "option_type": "INVALID",  # Invalid type
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/estimate", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_target_price_endpoint():
    """Test POST /api/v1/options/target-price."""
    payload = {
        "entry_premium": 100.0,
        "target_profit_percent": 50.0,
        "quantity": 50,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/target-price", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["entry_premium"] == 100.0
    assert data["required_exit_premium"] == 150.0
    assert data["gross_profit_per_unit"] == 50.0
    assert data["gross_pnl"] == 2500.0


@pytest.mark.asyncio
async def test_required_spot_endpoint_solution_found(future_expiry_iso: str):
    """Test POST /api/v1/options/required-spot finds a valid root for Call."""
    payload = {
        "underlying_symbol": "NIFTY",
        "strike_price": 24600.0,
        "option_type": "CE",
        "target_premium": 250.0,
        "expiry": future_expiry_iso,
        "time_to_expiry_minutes": 2880.0,  # 2 days
        "implied_volatility_percent": 13.5,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/required-spot", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["solver_status"] == "solution_found"
    assert data["required_spot"] is not None
    assert data["required_spot"] > 24600.0  # Deep ITM required to hit 250 premium


@pytest.mark.asyncio
async def test_required_spot_endpoint_unattainable_put(future_expiry_iso: str):
    """Test POST /api/v1/options/required-spot handles unattainable Put targets cleanly."""
    payload = {
        "underlying_symbol": "NIFTY",
        "strike_price": 24000.0,
        "option_type": "PE",
        "target_premium": 30000.0,  # Target premium > Strike price! Impossible for European put
        "expiry": future_expiry_iso,
        "time_to_expiry_minutes": 1440.0,
        "implied_volatility_percent": 15.0,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/required-spot", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["solver_status"] == "unattainable_target"
    assert data["required_spot"] is None
    assert "exceeds" in data["message"].lower()


@pytest.mark.asyncio
async def test_greeks_endpoint(future_expiry_iso: str):
    """Test POST /api/v1/options/greeks returns accurate Greeks."""
    payload = {
        "underlying_symbol": "NIFTY",
        "spot_price": 24500.0,
        "strike_price": 24600.0,
        "option_type": "CE",
        "expiry": future_expiry_iso,
        "implied_volatility_percent": 13.5,
        "risk_free_rate_percent": 7.0,
        "dividend_yield_percent": 1.2,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/options/greeks", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["spot_price"] == 24500.0
    assert data["greeks"]["delta"] is not None
    assert 0.0 < data["greeks"]["delta"] < 1.0
    assert data["greeks"]["gamma"] > 0.0
    assert data["greeks"]["vega"] > 0.0


@pytest.mark.asyncio
async def test_openapi_schema_contains_all_v1_endpoints():
    """Verify that the OpenAPI JSON schema exposes all 5 core endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    assert "/health" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/options/estimate" in paths
    assert "/api/v1/options/target-price" in paths
    assert "/api/v1/options/required-spot" in paths
    assert "/api/v1/options/greeks" in paths

