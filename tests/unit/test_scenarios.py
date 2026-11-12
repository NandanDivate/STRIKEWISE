"""Unit tests for IV scenario analysis."""

import pytest

from app.pricing.scenarios import MINIMUM_IV_PERCENT, generate_iv_scenarios


def test_scenario_order_and_naming():
    """Scenarios must contain conservative, base, and optimistic in standard order."""
    scenarios, warnings = generate_iv_scenarios(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        base_iv_percent=14.0,
        option_type="CE",
        shift_percentage_points=2.0,
    )
    assert len(scenarios) == 3
    assert scenarios[0].scenario_name == "conservative"
    assert scenarios[1].scenario_name == "base"
    assert scenarios[2].scenario_name == "optimistic"

    # Check applied IV percentage points
    assert scenarios[0].iv_used_percent == 12.0
    assert scenarios[1].iv_used_percent == 14.0
    assert scenarios[2].iv_used_percent == 16.0
    assert len(warnings) == 0


def test_higher_iv_increases_premiums():
    """Optimistic (higher IV) must yield higher premium than conservative for long options."""
    scenarios_c, _ = generate_iv_scenarios(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        base_iv_percent=15.0,
        option_type="CE",
    )
    assert scenarios_c[0].estimated_premium < scenarios_c[1].estimated_premium
    assert scenarios_c[1].estimated_premium < scenarios_c[2].estimated_premium

    scenarios_p, _ = generate_iv_scenarios(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        base_iv_percent=15.0,
        option_type="PE",
    )
    assert scenarios_p[0].estimated_premium < scenarios_p[1].estimated_premium
    assert scenarios_p[1].estimated_premium < scenarios_p[2].estimated_premium


def test_clamping_for_low_iv():
    """If base IV minus shift is non-positive, it must clamp to MINIMUM_IV_PERCENT and issue a warning."""
    scenarios, warnings = generate_iv_scenarios(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        base_iv_percent=1.5,  # 1.5 - 2.0 = -0.5% (non-positive)
        option_type="CE",
        shift_percentage_points=2.0,
    )
    assert scenarios[0].iv_used_percent == MINIMUM_IV_PERCENT
    assert scenarios[0].estimated_premium >= 0.0
    assert len(warnings) > 0
    assert "clamped" in warnings[0].lower()

