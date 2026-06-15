"""
Custom exception classes for TradeAI domain errors.
"""


class TradeAIBaseException(Exception):
    message: str = "An error occurred"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(TradeAIBaseException):
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(msg)


class UnauthorizedError(TradeAIBaseException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)


class InsufficientFundsError(TradeAIBaseException):
    def __init__(self, required: float, available: float):
        super().__init__(f"Insufficient funds: required ${required:,.2f}, available ${available:,.2f}")


class InsufficientSharesError(TradeAIBaseException):
    def __init__(self, symbol: str, required: float, available: float):
        super().__init__(f"Insufficient shares for {symbol}: trying to sell {required}, holding {available:.4f}")


class InvalidOrderError(TradeAIBaseException):
    def __init__(self, message: str = "Invalid order parameters"):
        super().__init__(message)


class MarketDataError(TradeAIBaseException):
    def __init__(self, symbol: str, message: str = ""):
        base = f"Market data unavailable for {symbol}"
        super().__init__(f"{base}: {message}" if message else base)


class BacktestError(TradeAIBaseException):
    def __init__(self, message: str = "Backtesting failed"):
        super().__init__(message)
