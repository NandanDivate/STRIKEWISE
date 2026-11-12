"""Unit tests for package imports and developer public API."""

import pytest


def test_app_pricing_imports():
    """Verify that app.pricing exposes all expected core pricing functions."""
    from app.pricing import (
        OptionType,
        black_scholes_price,
        call_price,
        put_price,
        intrinsic_value,
        calculate_greeks,
        solve_required_spot,
        generate_iv_scenarios,
        to_year_fraction,
        MINIMUM_IV_PERCENT,
    )

    # Basic smoke calculation
    call = call_price(
        spot=24500.0,
        strike=24500.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
    )
    assert call > 0.0

    greeks = calculate_greeks(
        spot=24500.0,
        strike=24500.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
        option_type="CE",
    )
    assert 0.0 < greeks.delta < 1.0


def test_strikewise_top_level_imports():
    """Verify that strikewise top-level package can be imported directly."""
    import strikewise

    assert strikewise.__version__ == "1.0.0"
    assert strikewise.__license__ == "Apache-2.0"

    # Test function access
    put = strikewise.put_price(
        spot=24500.0,
        strike=24500.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
    )
    assert put > 0.0

    # Test solver
    spot, status, _ = strikewise.solve_required_spot(
        strike=24500.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
        option_type="CE",
        target_premium=put,
    )
    assert status == "solution_found"
    assert spot is not None
