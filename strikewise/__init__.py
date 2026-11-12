"""STRIKEWISE — Quantitative Options Pricing & Risk Engine for NIFTY.

A high-performance quantitative library and API service providing:
- European Black-Scholes-Merton option pricing with continuous dividend yield
- Analytical Greeks: Delta, Gamma, Theta (per-day), Vega (per 1% IV), Rho
- Inverse spot pricing using SciPy Brent's root-finding method
- Volatility scenario simulations (Conservative, Base, Optimistic)
- Strict ACT/365 day-count convention & timezone-aware time utilities
"""

__version__ = "1.0.0"
__author__ = "Nandan Divate"
__license__ = "Apache-2.0"

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
    "__version__",
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
