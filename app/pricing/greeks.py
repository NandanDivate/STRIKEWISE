"""Option Greeks calculation for Black-Scholes-Merton model with continuous dividends.

Computes analytical Delta, Gamma, Theta, Vega, and Rho for European options.

Documented Units:
    - Delta: Premium change per 1-point move in underlying index (unitless ratio).
    - Gamma: Change in Delta per 1-point move in underlying index (per point).
    - Theta: Premium change per calendar day (annual derivative / 365).
    - Vega: Premium change for a 1 percentage point move in implied volatility (e.g. 15% -> 16%).
    - Rho: Premium change for a 1 percentage point move in risk-free interest rate (e.g. 7% -> 8%).
"""

from __future__ import annotations

import math
from typing import Literal, Optional

from scipy.stats import norm

from app.core.errors import PricingError
from app.schemas.responses import GreeksResult


OptionType = Literal["CE", "PE"]


def calculate_greeks(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
    option_type: OptionType,
) -> GreeksResult:
    """Calculate analytical Black-Scholes-Merton Greeks for a European option.

    Args:
        spot: Underlying spot index level (> 0).
        strike: Option strike price (> 0).
        time_to_expiry_years: Time to expiry in years (ACT/365). If <= 0, returns boundary Greeks.
        risk_free_rate: Continuously compounded risk-free rate as decimal (e.g. 0.07).
        dividend_yield: Continuously compounded dividend yield as decimal (e.g. 0.012).
        volatility: Annualized implied volatility as decimal (e.g. 0.135).
        option_type: "CE" for Call or "PE" for Put.

    Returns:
        GreeksResult containing delta, gamma, theta, vega, rho.
    """
    if spot <= 0.0 or strike <= 0.0 or volatility <= 0.0:
        raise PricingError(
            "Spot, strike, and volatility must be strictly positive.",
            details={"spot": spot, "strike": strike, "volatility": volatility},
        )
    if option_type not in ("CE", "PE"):
        raise PricingError(f"Invalid option type '{option_type}'. Must be 'CE' or 'PE'.")

    # Boundary conditions at or beyond expiry (T <= 0)
    if time_to_expiry_years <= 0.0:
        if option_type == "CE":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if strike > spot else 0.0
        return GreeksResult(
            delta=delta,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
        )

    sqrt_t = math.sqrt(time_to_expiry_years)
    sigma_sqrt_t = volatility * sqrt_t

    if sigma_sqrt_t < 1e-12:
        # Near-zero time or volatility boundary
        if option_type == "CE":
            delta = math.exp(-dividend_yield * time_to_expiry_years) if spot > strike else 0.0
        else:
            delta = -math.exp(-dividend_yield * time_to_expiry_years) if strike > spot else 0.0
        return GreeksResult(
            delta=delta,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
        )

    # Standard d1 and d2
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility)
        * time_to_expiry_years
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)
    cdf_minus_d1 = norm.cdf(-d1)
    cdf_minus_d2 = norm.cdf(-d2)

    disc_s = math.exp(-dividend_yield * time_to_expiry_years)
    disc_k = math.exp(-risk_free_rate * time_to_expiry_years)

    # Delta: dV / dS
    if option_type == "CE":
        delta = disc_s * cdf_d1
    else:
        delta = -disc_s * cdf_minus_d1

    # Gamma: d^2V / dS^2 (same for Call and Put)
    gamma = (disc_s * pdf_d1) / (spot * sigma_sqrt_t)

    # Vega: dV / d_sigma (annual derivative), scaled per 1 percentage point IV move (/ 100)
    annual_vega = spot * disc_s * sqrt_t * pdf_d1
    vega = annual_vega / 100.0

    # Theta: -dV / dT (decay per calendar day = annual / 365)
    first_term = -(spot * disc_s * pdf_d1 * volatility) / (2.0 * sqrt_t)
    if option_type == "CE":
        annual_theta = (
            first_term
            - risk_free_rate * strike * disc_k * cdf_d2
            + dividend_yield * spot * disc_s * cdf_d1
        )
    else:
        annual_theta = (
            first_term
            + risk_free_rate * strike * disc_k * cdf_minus_d2
            - dividend_yield * spot * disc_s * cdf_minus_d1
        )
    theta = annual_theta / 365.0

    # Rho: dV / dr (annual derivative), scaled per 1 percentage point rate move (/ 100)
    if option_type == "CE":
        annual_rho = strike * time_to_expiry_years * disc_k * cdf_d2
    else:
        annual_rho = -strike * time_to_expiry_years * disc_k * cdf_minus_d2
    rho = annual_rho / 100.0

    return GreeksResult(
        delta=float(delta),
        gamma=float(gamma),
        theta=float(theta),
        vega=float(vega),
        rho=float(rho),
    )
