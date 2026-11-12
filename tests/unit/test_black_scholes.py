"""Unit tests for the Black-Scholes-Merton pricing engine.

Tests mathematical correctness, put-call parity, monotonicity, boundary conditions,
intrinsic value at expiry, and error handling for invalid/non-finite inputs.
"""

import math
import pytest

from app.core.errors import PricingError
from app.pricing.black_scholes import (
    black_scholes_price,
    call_price,
    put_price,
    intrinsic_value,
)


# ---------------------------------------------------------------------------
# Reference Benchmark Cases
# ---------------------------------------------------------------------------

def test_reference_call_price_without_dividends():
    """Test known benchmark Hull reference case (S=100, K=100, T=1, r=0.05, q=0, vol=0.20).
    
    Analytical value: ~10.4506 points.
    """
    price = call_price(
        spot=100.0,
        strike=100.0,
        time_to_expiry_years=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        volatility=0.20,
    )
    assert pytest.approx(price, rel=1e-4) == 10.4506


def test_reference_put_price_without_dividends():
    """Test known benchmark Hull reference case for put option.
    
    Analytical value: ~5.5735 points.
    """
    price = put_price(
        spot=100.0,
        strike=100.0,
        time_to_expiry_years=1.0,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        volatility=0.20,
    )
    assert pytest.approx(price, rel=1e-4) == 5.5735


def test_reference_nifty_realistic_scale():
    """Test realistic NIFTY option scale with continuous dividend yield:
    S = 24500, K = 24600, T = 14/365, r = 0.07, q = 0.012, vol = 0.135 (13.5%).
    """
    c = call_price(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=14.0 / 365.0,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.135,
    )
    p = put_price(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=14.0 / 365.0,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.135,
    )
    assert c > 0.0
    assert p > 0.0
    # For S=24500 and K=24600, Put is ITM so Put should be priced higher than Call
    assert p > c


# ---------------------------------------------------------------------------
# Put-Call Parity: C - P = S*exp(-q*T) - K*exp(-r*T)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "spot,strike,t_years,r,q,sigma",
    [
        (100.0, 100.0, 1.0, 0.05, 0.0, 0.20),
        (24500.0, 24600.0, 0.05, 0.07, 0.012, 0.135),
        (24500.0, 24000.0, 0.10, 0.065, 0.015, 0.18),
        (25000.0, 25500.0, 0.25, 0.07, 0.010, 0.11),
        (24000.0, 24000.0, 0.001, 0.07, 0.012, 0.15),
    ],
)
def test_put_call_parity_within_tolerance(spot, strike, t_years, r, q, sigma):
    """Verify that Put-Call parity holds within high floating point precision."""
    c = call_price(spot, strike, t_years, r, q, sigma)
    p = put_price(spot, strike, t_years, r, q, sigma)

    left_side = c - p
    right_side = spot * math.exp(-q * t_years) - strike * math.exp(-r * t_years)

    assert pytest.approx(left_side, abs=1e-8) == right_side


# ---------------------------------------------------------------------------
# Monotonicity Tests
# ---------------------------------------------------------------------------

def test_call_price_increases_with_spot():
    """All else equal, a Call price must strictly increase as spot increases."""
    spots = [24000.0, 24200.0, 24500.0, 24800.0, 25000.0]
    prices = [
        call_price(s, strike=24500.0, time_to_expiry_years=0.08, risk_free_rate=0.07, dividend_yield=0.012, volatility=0.14)
        for s in spots
    ]
    for i in range(len(prices) - 1):
        assert prices[i + 1] > prices[i]


def test_put_price_decreases_with_spot():
    """All else equal, a Put price must strictly decrease as spot increases."""
    spots = [24000.0, 24200.0, 24500.0, 24800.0, 25000.0]
    prices = [
        put_price(s, strike=24500.0, time_to_expiry_years=0.08, risk_free_rate=0.07, dividend_yield=0.012, volatility=0.14)
        for s in spots
    ]
    for i in range(len(prices) - 1):
        assert prices[i + 1] < prices[i]


def test_options_increase_with_volatility():
    """Vanilla European Call and Put prices must strictly increase with volatility."""
    vols = [0.10, 0.12, 0.15, 0.20, 0.25]
    calls = [
        call_price(spot=24500.0, strike=24500.0, time_to_expiry_years=0.05, risk_free_rate=0.07, dividend_yield=0.012, volatility=v)
        for v in vols
    ]
    puts = [
        put_price(spot=24500.0, strike=24500.0, time_to_expiry_years=0.05, risk_free_rate=0.07, dividend_yield=0.012, volatility=v)
        for v in vols
    ]
    for i in range(len(vols) - 1):
        assert calls[i + 1] > calls[i]
        assert puts[i + 1] > puts[i]


# ---------------------------------------------------------------------------
# Intrinsic Value at or Past Expiry
# ---------------------------------------------------------------------------

def test_call_intrinsic_value_at_expiry():
    """At T <= 0, Call option returns max(S - K, 0)."""
    assert black_scholes_price(24700.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "CE") == 200.0
    assert black_scholes_price(24500.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "CE") == 0.0
    assert black_scholes_price(24300.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "CE") == 0.0
    # Negative time also evaluates to intrinsic value
    assert black_scholes_price(24700.0, 24500.0, -0.01, 0.07, 0.012, 0.15, "CE") == 200.0


def test_put_intrinsic_value_at_expiry():
    """At T <= 0, Put option returns max(K - S, 0)."""
    assert black_scholes_price(24300.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "PE") == 200.0
    assert black_scholes_price(24500.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "PE") == 0.0
    assert black_scholes_price(24700.0, 24500.0, 0.0, 0.07, 0.012, 0.15, "PE") == 0.0
    # Negative time also evaluates to intrinsic value
    assert black_scholes_price(24300.0, 24500.0, -0.05, 0.07, 0.012, 0.15, "PE") == 200.0


# ---------------------------------------------------------------------------
# Deep ITM and Deep OTM Asymptotics
# ---------------------------------------------------------------------------

def test_deep_itm_and_otm_call():
    """Deep ITM call approaches S*exp(-qT) - K*exp(-rT); Deep OTM call approaches 0."""
    t_years = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.15

    # Deep ITM (S=50000, K=10000)
    c_itm = call_price(50000.0, 10000.0, t_years, r, q, sigma)
    expected_itm = 50000.0 * math.exp(-q * t_years) - 10000.0 * math.exp(-r * t_years)
    assert pytest.approx(c_itm, rel=1e-5) == expected_itm

    # Deep OTM (S=10000, K=50000)
    c_otm = call_price(10000.0, 50000.0, t_years, r, q, sigma)
    assert pytest.approx(c_otm, abs=1e-8) == 0.0


def test_deep_itm_and_otm_put():
    """Deep ITM put approaches K*exp(-rT) - S*exp(-qT); Deep OTM put approaches 0."""
    t_years = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.15

    # Deep ITM (S=10000, K=50000)
    p_itm = put_price(10000.0, 50000.0, t_years, r, q, sigma)
    expected_itm = 50000.0 * math.exp(-r * t_years) - 10000.0 * math.exp(-q * t_years)
    assert pytest.approx(p_itm, rel=1e-5) == expected_itm

    # Deep OTM (S=50000, K=10000)
    p_otm = put_price(50000.0, 10000.0, t_years, r, q, sigma)
    assert pytest.approx(p_otm, abs=1e-8) == 0.0


# ---------------------------------------------------------------------------
# Near-Expiry Numerical Stability
# ---------------------------------------------------------------------------

def test_near_expiry_numerical_stability():
    """Option with tiny remaining time (e.g. 1 minute = ~1.9e-6 years) evaluates safely."""
    one_minute_years = 1.0 / (365.0 * 24.0 * 60.0)
    # ATM option
    c_atm = call_price(24500.0, 24500.0, one_minute_years, 0.07, 0.012, 0.15)
    p_atm = put_price(24500.0, 24500.0, one_minute_years, 0.07, 0.012, 0.15)
    assert c_atm >= 0.0
    assert p_atm >= 0.0
    # ITM call by 50 points
    c_itm = call_price(24550.0, 24500.0, one_minute_years, 0.07, 0.012, 0.15)
    assert pytest.approx(c_itm, abs=1.0) == 50.0


# ---------------------------------------------------------------------------
# Input Validation and Edge Case Error Handling
# ---------------------------------------------------------------------------

def test_invalid_spot_raises_pricing_error():
    with pytest.raises(PricingError, match="Spot price must be strictly positive"):
        call_price(0.0, 24500.0, 0.1, 0.07, 0.012, 0.15)

    with pytest.raises(PricingError, match="Spot price must be strictly positive"):
        call_price(-24500.0, 24500.0, 0.1, 0.07, 0.012, 0.15)


def test_invalid_strike_raises_pricing_error():
    with pytest.raises(PricingError, match="Strike price must be strictly positive"):
        call_price(24500.0, 0.0, 0.1, 0.07, 0.012, 0.15)

    with pytest.raises(PricingError, match="Strike price must be strictly positive"):
        call_price(24500.0, -24500.0, 0.1, 0.07, 0.012, 0.15)


def test_invalid_volatility_raises_pricing_error():
    with pytest.raises(PricingError, match="Volatility must be strictly positive"):
        call_price(24500.0, 24500.0, 0.1, 0.07, 0.012, 0.0)

    with pytest.raises(PricingError, match="Volatility must be strictly positive"):
        call_price(24500.0, 24500.0, 0.1, 0.07, 0.012, -0.15)


def test_non_finite_inputs_raise_pricing_error():
    with pytest.raises(PricingError, match="must be a finite number"):
        call_price(float("nan"), 24500.0, 0.1, 0.07, 0.012, 0.15)

    with pytest.raises(PricingError, match="must be a finite number"):
        call_price(24500.0, float("inf"), 0.1, 0.07, 0.012, 0.15)

    with pytest.raises(PricingError, match="must be a finite number"):
        call_price(24500.0, 24500.0, float("-inf"), 0.07, 0.012, 0.15)


def test_invalid_option_type_raises_pricing_error():
    with pytest.raises(PricingError, match="Invalid option type 'CALL'"):
        black_scholes_price(24500.0, 24500.0, 0.1, 0.07, 0.012, 0.15, "CALL")  # type: ignore

    with pytest.raises(PricingError, match="Invalid option type 'FOO'"):
        intrinsic_value(24500.0, 24500.0, "FOO")  # type: ignore

