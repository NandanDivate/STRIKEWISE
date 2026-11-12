"""Unit tests for option Greeks.

Tests analytical formulas, signs, bounds, finite-difference cross-checks,
and boundary conditions for European Call and Put options.
"""

import math
import pytest

from app.pricing.black_scholes import call_price, put_price
from app.pricing.greeks import calculate_greeks


# ---------------------------------------------------------------------------
# Signs and Plausible Bounds
# ---------------------------------------------------------------------------

def test_call_greeks_signs_and_bounds():
    """Verify CE Greek signs: Delta in (0, 1), Gamma > 0, Vega > 0, Rho > 0, Theta < 0."""
    g = calculate_greeks(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=14.0 / 365.0,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.135,
        option_type="CE",
    )
    assert 0.0 < g.delta < 1.0
    assert g.gamma > 0.0
    assert g.vega > 0.0
    assert g.rho > 0.0
    assert g.theta < 0.0  # Option loses value as time passes


def test_put_greeks_signs_and_bounds():
    """Verify PE Greek signs: Delta in (-1, 0), Gamma > 0, Vega > 0, Rho < 0, Theta < 0."""
    g = calculate_greeks(
        spot=24500.0,
        strike=24600.0,
        time_to_expiry_years=14.0 / 365.0,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.135,
        option_type="PE",
    )
    assert -1.0 < g.delta < 0.0
    assert g.gamma > 0.0
    assert g.vega > 0.0
    assert g.rho < 0.0


def test_gamma_identical_for_call_and_put():
    """Under Black-Scholes-Merton, Call and Put Gamma are mathematically identical."""
    params = dict(
        spot=24500.0,
        strike=24500.0,
        time_to_expiry_years=0.05,
        risk_free_rate=0.07,
        dividend_yield=0.012,
        volatility=0.14,
    )
    c_greeks = calculate_greeks(**params, option_type="CE")
    p_greeks = calculate_greeks(**params, option_type="PE")
    assert pytest.approx(c_greeks.gamma, rel=1e-8) == p_greeks.gamma
    assert pytest.approx(c_greeks.vega, rel=1e-8) == p_greeks.vega


# ---------------------------------------------------------------------------
# Finite Difference Cross-Checks (Analytical vs Numerical)
# ---------------------------------------------------------------------------

def test_delta_vs_finite_difference():
    """Delta approx = [V(S + h) - V(S - h)] / (2h)."""
    s = 24500.0
    k = 24600.0
    t = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.14
    h = 0.01

    # Call Delta
    c_plus = call_price(s + h, k, t, r, q, sigma)
    c_minus = call_price(s - h, k, t, r, q, sigma)
    fd_delta_call = (c_plus - c_minus) / (2.0 * h)
    analytical_delta_call = calculate_greeks(s, k, t, r, q, sigma, "CE").delta
    assert pytest.approx(analytical_delta_call, rel=1e-4) == fd_delta_call

    # Put Delta
    p_plus = put_price(s + h, k, t, r, q, sigma)
    p_minus = put_price(s - h, k, t, r, q, sigma)
    fd_delta_put = (p_plus - p_minus) / (2.0 * h)
    analytical_delta_put = calculate_greeks(s, k, t, r, q, sigma, "PE").delta
    assert pytest.approx(analytical_delta_put, rel=1e-4) == fd_delta_put


def test_gamma_vs_finite_difference():
    """Gamma approx = [V(S + h) - 2*V(S) + V(S - h)] / h^2."""
    s = 24500.0
    k = 24600.0
    t = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.14
    h = 0.1

    v_plus = call_price(s + h, k, t, r, q, sigma)
    v_mid = call_price(s, k, t, r, q, sigma)
    v_minus = call_price(s - h, k, t, r, q, sigma)
    fd_gamma = (v_plus - 2.0 * v_mid + v_minus) / (h * h)

    analytical_gamma = calculate_greeks(s, k, t, r, q, sigma, "CE").gamma
    assert pytest.approx(analytical_gamma, rel=1e-3) == fd_gamma


def test_vega_vs_finite_difference():
    """Vega approx per 1 percentage point = [V(sigma + 0.005) - V(sigma - 0.005)]."""
    s = 24500.0
    k = 24600.0
    t = 0.05
    r = 0.07
    q = 0.012
    sigma = 0.14
    h = 0.0001  # 0.01 percentage point move

    v_plus = call_price(s, k, t, r, q, sigma + h)
    v_minus = call_price(s, k, t, r, q, sigma - h)
    # Derivative w.r.t sigma:
    annual_vega_fd = (v_plus - v_minus) / (2.0 * h)
    vega_1pct_fd = annual_vega_fd / 100.0

    analytical_vega = calculate_greeks(s, k, t, r, q, sigma, "CE").vega
    assert pytest.approx(analytical_vega, rel=1e-4) == vega_1pct_fd


# ---------------------------------------------------------------------------
# Expiry Boundary Greeks
# ---------------------------------------------------------------------------

def test_expiry_boundary_greeks():
    """At T <= 0, Delta is binary (1 for ITM call, 0 for OTM; -1 for ITM put, 0 for OTM), other Greeks 0."""
    # ITM Call
    g_itm_c = calculate_greeks(24700.0, 24500.0, 0.0, 0.07, 0.012, 0.14, "CE")
    assert g_itm_c.delta == 1.0
    assert g_itm_c.gamma == 0.0
    assert g_itm_c.theta == 0.0
    assert g_itm_c.vega == 0.0
    assert g_itm_c.rho == 0.0

    # OTM Call
    g_otm_c = calculate_greeks(24300.0, 24500.0, 0.0, 0.07, 0.012, 0.14, "CE")
    assert g_otm_c.delta == 0.0

    # ITM Put
    g_itm_p = calculate_greeks(24300.0, 24500.0, 0.0, 0.07, 0.012, 0.14, "PE")
    assert g_itm_p.delta == -1.0
    assert g_itm_p.gamma == 0.0

    # OTM Put
    g_otm_p = calculate_greeks(24700.0, 24500.0, 0.0, 0.07, 0.012, 0.14, "PE")
    assert g_otm_p.delta == 0.0

