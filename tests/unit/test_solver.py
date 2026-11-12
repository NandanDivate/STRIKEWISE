"""Unit tests for the reverse option pricing solver.

Tests Brent's method root-finding, safe dynamic bracketing, Put attainability limits,
repricing accuracy, and error handling for invalid/extreme target premiums.
"""

import math
import pytest

from app.core.errors import PricingError
from app.pricing.black_scholes import black_scholes_price
from app.pricing.solver import solve_required_spot


# ---------------------------------------------------------------------------
# Valid Call and Put Solutions
# ---------------------------------------------------------------------------

def test_solve_call_valid_root():
    """Verify solver finds an accurate underlying spot for a standard Call target."""
    strike = 24600.0
    t_years = 14.0 / 365.0
    r = 0.07
    q = 0.012
    sigma = 0.135
    target = 250.0

    spot, status, msg = solve_required_spot(
        strike=strike,
        time_to_expiry_years=t_years,
        risk_free_rate=r,
        dividend_yield=q,
        volatility=sigma,
        option_type="CE",
        target_premium=target,
    )

    assert status == "solution_found"
    assert spot is not None

    # Verify repricing matches target within tight tolerance
    repriced = black_scholes_price(spot, strike, t_years, r, q, sigma, "CE")
    assert pytest.approx(repriced, abs=1e-4) == target


def test_solve_put_valid_root():
    """Verify solver finds an accurate underlying spot for a standard Put target."""
    strike = 24500.0
    t_years = 14.0 / 365.0
    r = 0.07
    q = 0.012
    sigma = 0.135
    target = 350.0  # ITM target (ATM put is ~231.7, so 350 requires spot < strike)

    spot, status, msg = solve_required_spot(
        strike=strike,
        time_to_expiry_years=t_years,
        risk_free_rate=r,
        dividend_yield=q,
        volatility=sigma,
        option_type="PE",
        target_premium=target,
    )

    assert status == "solution_found"
    assert spot is not None
    assert spot < strike  # Must be ITM (spot below strike) for Put

    # Verify repricing
    repriced = black_scholes_price(spot, strike, t_years, r, q, sigma, "PE")
    assert pytest.approx(repriced, abs=1e-4) == target


# ---------------------------------------------------------------------------
# Dynamic Bracketing: Beyond Naive 0.70x - 1.30x Search Range
# ---------------------------------------------------------------------------

def test_solve_call_large_target_beyond_narrow_multiplier():
    """A very large target premium requires spot > 1.5x strike.
    
    A naive fixed [0.7*S, 1.3*S] search bracket would fail here.
    Dynamic bracketing must successfully expand and bracket the root.
    """
    strike = 100.0
    t_years = 0.5
    r = 0.05
    q = 0.0
    sigma = 0.20
    target = 300.0  # Requires spot around ~400+ (4x strike)

    spot, status, msg = solve_required_spot(
        strike=strike,
        time_to_expiry_years=t_years,
        risk_free_rate=r,
        dividend_yield=q,
        volatility=sigma,
        option_type="CE",
        target_premium=target,
    )

    assert status == "solution_found"
    assert spot is not None
    assert spot > 350.0  # Far outside any narrow 1.30x bracket

    repriced = black_scholes_price(spot, strike, t_years, r, q, sigma, "CE")
    assert pytest.approx(repriced, abs=1e-4) == target


def test_solve_call_tiny_target_premium():
    """A tiny target premium (e.g. 0.05 points) requires spot far below strike."""
    strike = 24500.0
    t_years = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.14
    target = 0.05

    spot, status, msg = solve_required_spot(
        strike=strike,
        time_to_expiry_years=t_years,
        risk_free_rate=r,
        dividend_yield=q,
        volatility=sigma,
        option_type="CE",
        target_premium=target,
    )

    assert status == "solution_found"
    assert spot is not None
    assert spot < strike

    repriced = black_scholes_price(spot, strike, t_years, r, q, sigma, "CE")
    assert pytest.approx(repriced, abs=1e-3) == target


# ---------------------------------------------------------------------------
# Mathematical Unattainability for Puts
# ---------------------------------------------------------------------------

def test_unattainable_put_target_exceeds_maximum_bound():
    """For a European Put, theoretical premium cannot exceed K * exp(-r*T).
    
    If target >= K * exp(-r*T), the solver must return 'unattainable_target' and None.
    """
    strike = 20000.0
    t_years = 1.0
    r = 0.08
    q = 0.01
    sigma = 0.15

    max_possible_put = strike * math.exp(-r * t_years)  # ~18462.3
    impossible_target = max_possible_put + 100.0

    spot, status, msg = solve_required_spot(
        strike=strike,
        time_to_expiry_years=t_years,
        risk_free_rate=r,
        dividend_yield=q,
        volatility=sigma,
        option_type="PE",
        target_premium=impossible_target,
    )

    assert status == "unattainable_target"
    assert spot is None
    assert "exceeds the maximum theoretical Put value" in msg


def test_put_target_above_strike_unattainable():
    """A target premium greater than the strike itself is always unattainable."""
    spot, status, msg = solve_required_spot(
        strike=24000.0,
        time_to_expiry_years=0.1,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
        option_type="PE",
        target_premium=25000.0,
    )

    assert status == "unattainable_target"
    assert spot is None


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------

def test_solve_required_spot_invalid_target_premium():
    """Zero or negative target premium raises PricingError."""
    with pytest.raises(PricingError, match="Target premium must be strictly positive"):
        solve_required_spot(24600.0, 0.05, 0.07, 0.012, 0.14, "CE", 0.0)

    with pytest.raises(PricingError, match="Target premium must be strictly positive"):
        solve_required_spot(24600.0, 0.05, 0.07, 0.012, 0.14, "CE", -50.0)


def test_solve_required_spot_invalid_strike_or_vol():
    """Non-positive strike or volatility raises PricingError."""
    with pytest.raises(PricingError, match="Strike and volatility must be strictly positive"):
        solve_required_spot(0.0, 0.05, 0.07, 0.012, 0.14, "CE", 100.0)

    with pytest.raises(PricingError, match="Strike and volatility must be strictly positive"):
        solve_required_spot(24600.0, 0.05, 0.07, 0.012, 0.0, "CE", 100.0)


def test_solve_required_spot_invalid_option_type():
    with pytest.raises(PricingError, match="Invalid option type 'INVALID'"):
        solve_required_spot(24600.0, 0.05, 0.07, 0.012, 0.14, "INVALID", 100.0)  # type: ignore
