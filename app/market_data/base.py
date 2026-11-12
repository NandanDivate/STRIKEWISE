"""Market data provider protocol (abstract interface).

Defines the contract that all market data providers must satisfy.
This allows the application to swap between manual input and live
data providers without changing business logic.
"""

from typing import Any, Dict, Optional, Protocol


class MarketDataProvider(Protocol):
    """Protocol defining the market data provider interface.

    All market data providers must implement these methods.
    Manual mode passes through user-supplied values.
    Live providers fetch from broker/exchange APIs.
    """

    def get_spot_quote(self, symbol: str) -> Dict[str, Any]:
        """Get the current spot price quote for a symbol.

        Args:
            symbol: The underlying symbol (e.g., "NIFTY").

        Returns:
            Dictionary with at minimum:
                - price: float
                - timestamp: datetime (quote time)
                - source: str (provider name)
        """
        ...

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        """Get the option chain for a symbol.

        Args:
            symbol: The underlying symbol (e.g., "NIFTY").

        Returns:
            Dictionary containing available strikes, expiries,
            and option instrument identifiers.
        """
        ...

    def get_option_quote(self, instrument_id: str) -> Dict[str, Any]:
        """Get a quote for a specific option instrument.

        Args:
            instrument_id: The unique instrument identifier.

        Returns:
            Dictionary with at minimum:
                - premium: float (last traded price or mid)
                - timestamp: datetime (quote time)
                - source: str (provider name)
                - iv: Optional[float] (implied volatility if available)
        """
        ...

