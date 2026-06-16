"""
Custom exception classes for TradeAI domain errors.
All exceptions expose a `.message` attribute for use in router error handlers.
"""


class TradeAIBaseException(Exception):
    """Base exception for all TradeAI domain errors."""
    message: str = "An error occurred"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(TradeAIBaseException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(msg)


class UnauthorizedError(TradeAIBaseException):
    """Raised when authentication fails or user lacks permission."""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)


class InsufficientFundsError(TradeAIBaseException):
    """Raised when user doesn't have enough balance for a trade."""

    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient funds: required ${required:,.2f}, "
            f"available ${available:,.2f}"
        )


class InsufficientSharesError(TradeAIBaseException):
    """Raised when user tries to sell more shares than they hold."""

    def __init__(self, symbol: str, required: float, available: float):
        super().__init__(
            f"Insufficient shares for {symbol}: "
            f"trying to sell {required}, holding {available:.4f}"
        )


class InvalidOrderError(TradeAIBaseException):
    """Raised when an order has invalid parameters."""

    def __init__(self, message: str = "Invalid order parameters"):
        super().__init__(message)


class MarketDataError(TradeAIBaseException):
    """Raised when market data cannot be fetched or is unavailable."""

    def __init__(self, symbol: str, message: str = ""):
        base = f"Market data unavailable for {symbol}"
        super().__init__(f"{base}: {message}" if message else base)


class BacktestError(TradeAIBaseException):
    """Raised when backtesting fails."""

    def __init__(self, message: str = "Backtesting failed"):
        super().__init__(message)
