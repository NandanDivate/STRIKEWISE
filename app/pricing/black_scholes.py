"""Black-Scholes-Merton option pricing model.

Implements European option pricing with continuous dividend yield:
    d1 = [ln(S/K) + (r - q + 0.5*sigma^2)*T] / (sigma*sqrt(T))
    d2 = d1 - sigma*sqrt(T)

    Call = S*exp(-q*T)*N(d1) - K*exp(-r*T)*N(d2)
    Put  = K*exp(-r*T)*N(-d2) - S*exp(-q*T)*N(-d1)

Where:
    S = underlying spot price
    K = strike price
    T = time to expiry in years
    r = continuously compounded annual risk-free rate as decimal
    q = continuously compounded annual dividend yield as decimal
    sigma = annualized volatility as decimal
    N = standard normal cumulative distribution function
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from scipy.stats import norm

from app.core.errors import PricingError


OptionType = Literal["CE", "PE"]


def intrinsic_value(spot: float, strike: float, option_type: OptionType) -> float:
    """Calculate the intrinsic value of a European option at or beyond expiry.

    Args:
        spot: Underlying spot index level (must be positive).
        strike: Option strike price (must be positive).
        option_type: "CE" for Call or "PE" for Put.

    Returns:
        Intrinsic value in index/premium points (non-negative float).
    """
    if option_type == "CE":
        return max(float(spot - strike), 0.0)
    elif option_type == "PE":
        return max(float(strike - spot), 0.0)
    else:
        raise PricingError(
            f"Invalid option type '{option_type}'. Must be 'CE' or 'PE'.",
            details={"option_type": option_type},
        )


def _validate_inputs(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
    option_type: str,
) -> None:
    """Validate numerical inputs to ensure finite values and valid domain."""
    params = {
        "spot": spot,
        "strike": strike,
        "time_to_expiry_years": time_to_expiry_years,
        "risk_free_rate": risk_free_rate,
        "dividend_yield": dividend_yield,
        "volatility": volatility,
    }

    # Check finite numbers
    for name, val in params.items():
        if val is None or not math.isfinite(val):
            raise PricingError(
                f"Parameter '{name}' must be a finite number, got {val}.",
                details={"parameter": name, "value": str(val)},
            )

    if spot <= 0.0:
        raise PricingError(
            f"Spot price must be strictly positive, got {spot}.",
            details={"spot": spot},
        )
    if strike <= 0.0:
        raise PricingError(
            f"Strike price must be strictly positive, got {strike}.",
            details={"strike": strike},
        )
    if volatility <= 0.0:
        raise PricingError(
            f"Volatility must be strictly positive, got {volatility}.",
            details={"volatility": volatility},
        )
    if option_type not in ("CE", "PE"):
        raise PricingError(
            f"Invalid option type '{option_type}'. Must be 'CE' or 'PE'.",
            details={"option_type": option_type},
        )


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
    option_type: OptionType,
) -> float:
    """Price a European option using Black-Scholes-Merton with continuous dividend yield.

    Args:
        spot: Underlying spot index level (e.g. 24500.0).
        strike: Option strike price (e.g. 24600.0).
        time_to_expiry_years: Time to expiry in years using ACT/365 (e.g. 0.05).
                              If <= 0, returns intrinsic value.
        risk_free_rate: Continuously compounded risk-free rate as decimal (e.g. 0.07 for 7%).
        dividend_yield: Continuously compounded dividend yield as decimal (e.g. 0.012 for 1.2%).
        volatility: Annualized implied volatility as decimal (e.g. 0.135 for 13.5%).
        option_type: "CE" for Call or "PE" for Put.

    Returns:
        Theoretical option premium in points/rupees.

    Raises:
        PricingError: If any parameter is invalid, non-finite, or mathematically out of bounds.
    """
    _validate_inputs(
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        option_type=option_type,
    )

    # At or past expiry, option value is intrinsic value
    if time_to_expiry_years <= 0.0:
        return intrinsic_value(spot, strike, option_type)

    # Numerical safeguard: if sigma * sqrt(T) is effectively zero
    sqrt_t = math.sqrt(time_to_expiry_years)
    sigma_sqrt_t = volatility * sqrt_t

    if sigma_sqrt_t < 1e-12:
        # Near-zero volatility or time: discounted forward intrinsic value
        disc_spot = spot * math.exp(-dividend_yield * time_to_expiry_years)
        disc_strike = strike * math.exp(-risk_free_rate * time_to_expiry_years)
        if option_type == "CE":
            return max(disc_spot - disc_strike, 0.0)
        else:
            return max(disc_strike - disc_spot, 0.0)

    # Standard BSM d1 and d2 calculations
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility)
        * time_to_expiry_years
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t

    disc_s = spot * math.exp(-dividend_yield * time_to_expiry_years)
    disc_k = strike * math.exp(-risk_free_rate * time_to_expiry_years)

    if option_type == "CE":
        price = disc_s * norm.cdf(d1) - disc_k * norm.cdf(d2)
    elif option_type == "PE":
        price = disc_k * norm.cdf(-d2) - disc_s * norm.cdf(-d1)
    else:
        raise PricingError(f"Unsupported option type '{option_type}'.")

    # Options cannot trade below zero
    return max(float(price), 0.0)


def call_price(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
) -> float:
    """Convenience function to price a European Call option (CE)."""
    return black_scholes_price(
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        option_type="CE",
    )


def put_price(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
) -> float:
    """Convenience function to price a European Put option (PE)."""
    return black_scholes_price(
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        option_type="PE",
    )
