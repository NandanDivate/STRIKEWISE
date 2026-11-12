"""Unit tests for exception handlers and convenience pricing wrappers."""

import pytest
from starlette.requests import Request

from app.core.errors import (
    ErrorResponse,
    MarketDataError,
    PricingError,
    SolverError,
    ValidationError,
    register_exception_handlers,
)
from app.main import app
from app.pricing.black_scholes import call_price, put_price


def test_black_scholes_convenience_wrappers():
    """Verify call_price and put_price convenience wrappers."""
    c = call_price(24500.0, 24600.0, 0.05, 0.07, 0.012, 0.135)
    p = put_price(24500.0, 24600.0, 0.05, 0.07, 0.012, 0.135)
    assert c > 0.0
    assert p > 0.0


@pytest.mark.asyncio
async def test_domain_exception_handlers():
    """Directly test that domain exception handlers return structured JSON."""
    scope = {"type": "http", "method": "GET", "path": "/test", "headers": []}
    req = Request(scope)

    # Find registered handlers
    handlers = app.exception_handlers

    # ValidationError -> 400
    val_handler = handlers.get(ValidationError)
    val_resp = await val_handler(req, ValidationError("Invalid field", details={"field": "test"}))
    assert val_resp.status_code == 400

    # PricingError -> 400
    pricing_handler = handlers.get(PricingError)
    pricing_resp = await pricing_handler(req, PricingError("Math error"))
    assert pricing_resp.status_code == 400

    # SolverError -> 400
    solver_handler = handlers.get(SolverError)
    solver_resp = await solver_handler(req, SolverError("Root failure"))
    assert solver_resp.status_code == 400

    # MarketDataError -> 503
    md_handler = handlers.get(MarketDataError)
    md_resp = await md_handler(req, MarketDataError("Gateway down"))
    assert md_resp.status_code == 503

    # Generic Exception -> 500
    gen_handler = handlers.get(Exception)
    gen_resp = await gen_handler(req, RuntimeError("Crash"))
    assert gen_resp.status_code == 500
