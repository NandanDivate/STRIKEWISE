"""Manual market data provider.

Passes through user-supplied values from the API request without
fetching any external data. This provider requires no credentials
and always works offline.

No fake or fabricated market data is generated.
"""

from datetime import datetime, timezone
from typing import Any, Dict


class ManualMarketDataProvider:
    """Market data provider that uses request-supplied values.

    This provider simply passes through the values provided by the user
    in the API request. It does not fetch, fabricate, or simulate any
    market data.
    """

    def get_spot_quote(self, symbol: str) -> Dict[str, Any]:
        """Not applicable for manual mode.

        In manual mode, spot price is supplied directly in the request.

        Args:
            symbol: The underlying symbol.

        Returns:
            Dictionary indicating manual mode with no live data.
        """
        return {
            "price": None,
            "timestamp": datetime.now(timezone.utc),
            "source": "manual",
            "message": "Manual mode: spot price must be supplied in the request.",
        }

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        """Not applicable for manual mode.

        In manual mode, strike and expiry are supplied directly in the request.

        Args:
            symbol: The underlying symbol.

        Returns:
            Dictionary indicating manual mode with no live data.
        """
        return {
            "instruments": [],
            "timestamp": datetime.now(timezone.utc),
            "source": "manual",
            "message": "Manual mode: strike and expiry must be supplied in the request.",
        }

    def get_option_quote(self, instrument_id: str) -> Dict[str, Any]:
        """Not applicable for manual mode.

        In manual mode, premium and IV are supplied directly in the request.

        Args:
            instrument_id: The instrument identifier.

        Returns:
            Dictionary indicating manual mode with no live data.
        """
        return {
            "premium": None,
            "timestamp": datetime.now(timezone.utc),
            "source": "manual",
            "iv": None,
            "message": "Manual mode: premium and IV must be supplied in the request.",
        }

