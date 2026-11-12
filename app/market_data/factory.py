"""Market data provider factory."""

from __future__ import annotations

import os
from typing import Optional

from app.market_data.base import MarketDataProvider
from app.market_data.manual import ManualMarketDataProvider
from app.market_data.providers.dhan import DhanHQProvider


def get_market_data_provider(provider_type: Optional[str] = None) -> MarketDataProvider:
    """Return the configured market data provider.

    Defaults to ManualMarketDataProvider if provider_type is None or 'manual'.
    """
    mode = (provider_type or os.getenv("MARKET_DATA_PROVIDER", "manual")).lower()

    if mode == "dhan":
        return DhanHQProvider()
    else:
        return ManualMarketDataProvider()

