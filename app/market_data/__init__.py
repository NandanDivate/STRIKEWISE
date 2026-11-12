"""Market data package.

Provides abstract provider protocol, manual pass-through provider,
live broker adapter (DhanHQ), and provider factory.
"""

from app.market_data.base import (
    MarketDataProvider,
    OptionQuote,
    SpotQuote,
    is_quote_stale,
)
from app.market_data.factory import get_market_data_provider
from app.market_data.manual import ManualMarketDataProvider


__all__ = [
    "MarketDataProvider",
    "SpotQuote",
    "OptionQuote",
    "is_quote_stale",
    "ManualMarketDataProvider",
    "get_market_data_provider",
]
