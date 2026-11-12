"""STRIKEWISE Pricing Engine.

Core quantitative pricing modules for European options:
- Black-Scholes-Merton model with continuous dividend yield
- Analytical Greeks (Delta, Gamma, Theta, Vega, Rho)
- Dynamic SciPy Brent numerical root solver for inverse spot pricing
- Volatility scenario analysis (Conservative, Base, Optimistic)
- ACT/365 day-count convention time utilities
"""

from app.pricing.black_scholes import (
    OptionType,
    black_scholes_price,
    call_price,
    intrinsic_value,
    put_price,
)
from app.pricing.greeks import calculate_greeks
from app.pricing.scenarios import MINIMUM_IV_PERCENT, generate_iv_scenarios
from app.pricing.solver import solve_required_spot
from app.pricing.time_utils import (
    DAYS_PER_YEAR,
    SECONDS_PER_DAY,
    SECONDS_PER_YEAR,
    ensure_timezone_aware,
    to_year_fraction,
)

__all__ = [
    "OptionType",
    "black_scholes_price",
    "call_price",
    "put_price",
    "intrinsic_value",
    "calculate_greeks",
    "solve_required_spot",
    "generate_iv_scenarios",
    "MINIMUM_IV_PERCENT",
    "to_year_fraction",
    "ensure_timezone_aware",
    "DAYS_PER_YEAR",
    "SECONDS_PER_DAY",
    "SECONDS_PER_YEAR",
]
