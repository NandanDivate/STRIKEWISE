"""IV scenario analysis.

Generates conservative, base, and optimistic premium estimates by shifting
implied volatility in percentage points (absolute points, not relative %).

Default shifts:
    - Conservative: current IV - shift (default 2.0 percentage points)
    - Base: current IV (0.0 shift)
    - Optimistic: current IV + shift (default 2.0 percentage points)

Non-positive IV resulting from a negative shift is clamped to a minimum positive
value (0.01% = 0.0001) as documented in docs/assumptions.md.
"""

from __future__ import annotations

from typing import List, Literal, Tuple

from app.pricing.black_scholes import black_scholes_price
from app.schemas.responses import ScenarioPremium


MINIMUM_IV_PERCENT = 0.01  # Minimum clamped IV in percentage (0.01%)


def generate_iv_scenarios(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    base_iv_percent: float,
    option_type: Literal["CE", "PE"],
    shift_percentage_points: float = 2.0,
) -> Tuple[List[ScenarioPremium], List[str]]:
    """Generate conservative, base, and optimistic IV scenario premiums.

    Args:
        spot: Underlying spot index level (e.g. target_spot).
        strike: Option strike price.
        time_to_expiry_years: Remaining time to expiry in years.
        risk_free_rate: Continuously compounded risk-free rate as decimal.
        dividend_yield: Continuously compounded dividend yield as decimal.
        base_iv_percent: Implied volatility in percent (e.g. 15.0).
        option_type: "CE" or "PE".
        shift_percentage_points: Absolute percentage point shift (default 2.0).

    Returns:
        tuple of:
            - list of ScenarioPremium objects (conservative, base, optimistic)
            - list of warning strings (e.g. if IV was clamped)
    """
    warnings: List[str] = []

    # Scenario definitions: (name, shift, description_template)
    scenario_configs = [
        (
            "conservative",
            -abs(shift_percentage_points),
            f"IV decreased by {abs(shift_percentage_points):.1f} percentage points",
        ),
        (
            "base",
            0.0,
            "Base scenario with unchanged implied volatility",
        ),
        (
            "optimistic",
            abs(shift_percentage_points),
            f"IV increased by {abs(shift_percentage_points):.1f} percentage points",
        ),
    ]

    scenarios: List[ScenarioPremium] = []

    for name, shift, desc in scenario_configs:
        raw_iv = base_iv_percent + shift
        clamped = False

        if raw_iv < MINIMUM_IV_PERCENT:
            iv_used = MINIMUM_IV_PERCENT
            clamped = True
            warnings.append(
                f"{name.capitalize()} scenario IV of {raw_iv:.2f}% was clamped to "
                f"minimum allowable IV of {MINIMUM_IV_PERCENT:.2f}%."
            )
        else:
            iv_used = raw_iv

        # Convert IV percent to decimal for pricing engine
        iv_decimal = iv_used / 100.0

        estimated_prem = black_scholes_price(
            spot=spot,
            strike=strike,
            time_to_expiry_years=time_to_expiry_years,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=iv_decimal,
            option_type=option_type,
        )

        scenarios.append(
            ScenarioPremium(
                scenario_name=name,
                iv_used_percent=round(iv_used, 4),
                estimated_premium=round(estimated_prem, 4),
                description=desc,
            )
        )

    return scenarios, warnings
