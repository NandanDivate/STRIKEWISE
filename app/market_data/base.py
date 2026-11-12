"""Market data provider protocol and quote structures.

Defines the contract that all market data providers must satisfy (Protocol pattern).
Provides quote data models, stale-data detection, and safe provider abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


DEFAULT_STALE_THRESHOLD_SECONDS = 60.0


@dataclass
class SpotQuote:
    """Quote for an underlying index or equity."""

    symbol: str
    price: Optional[float]
    timestamp: datetime
    source: str
    is_stale: bool = False
    message: Optional[str] = None


@dataclass
class OptionQuote:
    """Quote for a specific option contract."""

    instrument_id: str
    symbol: str
    strike: float
    option_type: str
    expiry: datetime
    premium: Optional[float]
    timestamp: datetime
    source: str
    implied_volatility: Optional[float] = None
    is_stale: bool = False
    message: Optional[str] = None


def is_quote_stale(
    quote_time: datetime,
    threshold_seconds: float = DEFAULT_STALE_THRESHOLD_SECONDS,
    current_time: Optional[datetime] = None,
) -> bool:
    """Determine whether a quote timestamp is considered stale.

    Args:
        quote_time: Timestamp when the quote was generated (must be tz-aware).
        threshold_seconds: Maximum age in seconds before quote is marked stale.
        current_time: Comparison timestamp (defaults to current UTC time).

    Returns:
        True if quote age exceeds threshold_seconds, False otherwise.
    """
    now = current_time or datetime.now(quote_time.tzinfo or timezone.utc)
    if quote_time.tzinfo is None:
        quote_time = quote_time.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_seconds = (now - quote_time).total_seconds()
    return age_seconds > threshold_seconds


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol defining the market data provider interface."""

    def get_spot_quote(self, symbol: str) -> SpotQuote:
        """Fetch current spot quote for an underlying symbol."""
        ...

    def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch available option chain instruments for an underlying symbol."""
        ...

    def get_option_quote(self, instrument_id: str) -> OptionQuote:
        """Fetch a specific option contract quote."""
        ...
