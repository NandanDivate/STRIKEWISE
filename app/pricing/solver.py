"""Numerical solver for reverse option pricing problems.

Uses SciPy's Brent's method (scipy.optimize.brentq) to solve:
    BSM(S_required, K, T, r, q, sigma, option_type) - target_premium = 0

Features:
    - Safe dynamic bracketing (no fragile fixed 0.7 to 1.3 multiplier).
    - Detects mathematical unattainability (e.g. Put target >= K*exp(-rT)).
    - Verifies repricing error of the solved spot.
    - Returns structured solver status and informative messages.
"""

from __future__ import annotations

import math
from typing import Literal, Optional, Tuple

from scipy.optimize import brentq

from app.core.errors import PricingError
from app.pricing.black_scholes import black_scholes_price


OptionType = Literal["CE", "PE"]


def solve_required_spot(
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
    option_type: OptionType,
    target_premium: float,
    max_spot_limit: float = 1_000_000.0,
) -> Tuple[Optional[float], str, str]:
    """Find the underlying spot price required for an option to reach a target premium.

    Args:
        strike: Option strike price (> 0).
        time_to_expiry_years: Time to expiry in years (ACT/365).
        risk_free_rate: Continuously compounded risk-free rate as decimal.
        dividend_yield: Continuously compounded dividend yield as decimal.
        volatility: Annualized implied volatility as decimal (> 0).
        option_type: "CE" or "PE".
        target_premium: Target option premium to solve for (> 0).
        max_spot_limit: Maximum search ceiling for underlying spot.

    Returns:
        tuple of:
            - required_spot: Solved spot price as float, or None if no root exists.
            - solver_status: 'solution_found', 'unattainable_target', or 'no_solution_in_search_range'.
            - message: Human-readable explanation.
    """
    if target_premium <= 0.0:
        raise PricingError(
            "Target premium must be strictly positive.",
            details={"target_premium": target_premium},
        )
    if strike <= 0.0 or volatility <= 0.0:
        raise PricingError(
            "Strike and volatility must be strictly positive.",
            details={"strike": strike, "volatility": volatility},
        )
    if option_type not in ("CE", "PE"):
        raise PricingError(f"Invalid option type '{option_type}'.")

    # Objective function: f(S) = BSM(S) - target_premium
    def objective(spot_candidate: float) -> float:
        return black_scholes_price(
            spot=spot_candidate,
            strike=strike,
            time_to_expiry_years=time_to_expiry_years,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=volatility,
            option_type=option_type,
        ) - target_premium

    # -----------------------------------------------------------------------
    # Put Option Domain Analysis
    # -----------------------------------------------------------------------
    if option_type == "PE":
        # Maximum possible European Put value as S -> 0 is K * exp(-r * T)
        max_possible_put = strike * math.exp(-risk_free_rate * max(time_to_expiry_years, 0.0))
        if target_premium >= max_possible_put:
            return (
                None,
                "unattainable_target",
                f"Target premium of {target_premium:.2f} exceeds the maximum theoretical "
                f"Put value of {max_possible_put:.2f} (K * exp(-r*T)).",
            )

        # For Put: As S -> 0, f(S) > 0. As S -> inf, f(S) < 0.
        # Find lower bound a where f(a) > 0
        a = 0.001 * strike
        fa = objective(a)
        if fa <= 0.0:
            # Shift a closer to 0
            a = 1e-5 * strike
            fa = objective(a)
            if fa <= 0.0:
                return (
                    None,
                    "no_solution_in_search_range",
                    "Could not bracket root for Put near zero spot.",
                )

        # Expand upper bound b until f(b) < 0
        b = max(strike, 1.0)
        fb = objective(b)
        expansion_count = 0
        while fb > 0.0 and b < max_spot_limit and expansion_count < 30:
            b *= 1.8
            fb = objective(b)
            expansion_count += 1

        if fb > 0.0:
            return (
                None,
                "no_solution_in_search_range",
                f"Could not bracket root for Put within spot limit of {max_spot_limit}.",
            )

    # -----------------------------------------------------------------------
    # Call Option Domain Analysis
    # -----------------------------------------------------------------------
    else:
        # For Call: As S -> 0, f(S) < 0. As S -> inf, f(S) > 0.
        # Find lower bound a where f(a) < 0
        a = 0.001 * strike
        fa = objective(a)
        if fa >= 0.0:
            a = 1e-5 * strike
            fa = objective(a)
            if fa >= 0.0:
                return (
                    None,
                    "no_solution_in_search_range",
                    "Could not find lower bracket for Call option.",
                )

        # Expand upper bound b until f(b) > 0
        b = max(strike + target_premium * 2.0, strike * 1.5)
        fb = objective(b)
        expansion_count = 0
        while fb < 0.0 and b < max_spot_limit and expansion_count < 30:
            b *= 1.8
            fb = objective(b)
            expansion_count += 1

        if fb < 0.0:
            return (
                None,
                "no_solution_in_search_range",
                f"Required spot exceeds upper search limit of {max_spot_limit}.",
            )

    # -----------------------------------------------------------------------
    # Root Finding via Brent's Method
    # -----------------------------------------------------------------------
    try:
        root = brentq(objective, a, b, xtol=1e-8, rtol=1e-8, maxiter=100)
    except Exception as exc:
        return (
            None,
            "solver_error",
            f"Brent solver failed to converge: {str(exc)}",
        )

    # Verification: reprice at root
    reprice_val = black_scholes_price(
        spot=root,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        option_type=option_type,
    )
    repricing_error = abs(reprice_val - target_premium)

    if repricing_error > 1e-2:
        return (
            None,
            "verification_failed",
            f"Solved spot repricing error ({repricing_error:.4f}) exceeded tolerance.",
        )

    return (
        float(root),
        "solution_found",
        f"Solution found: underlying spot of {root:.2f} reproduces target premium within tolerance.",
    )
