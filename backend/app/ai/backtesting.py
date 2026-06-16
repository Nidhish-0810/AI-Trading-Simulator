"""
Backtesting engine: replay trading strategies against historical data.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from app.ai.indicators import (
    calculate_rsi, calculate_macd, calculate_sma, calculate_bollinger_bands
)
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    date: str
    action: str  # buy | sell
    price: float
    quantity: float
    value: float
    pnl: float = 0.0


@dataclass
class BacktestResult:
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    best_trade_pct: float
    worst_trade_pct: float
    equity_curve: List[dict] = field(default_factory=list)  # [{date, value}]
    trades: List[dict] = field(default_factory=list)
    error: Optional[str] = None


class BaseStrategy:
    """Abstract base class for trading strategies."""
    name = "base"

    def should_buy(self, df: pd.DataFrame, index: int) -> bool:
        raise NotImplementedError

    def should_sell(self, df: pd.DataFrame, index: int, entry_price: float) -> bool:
        raise NotImplementedError


class SMAcrossoverStrategy(BaseStrategy):
    """Buy when fast SMA crosses above slow SMA, sell on reverse."""
    name = "sma_crossover"

    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        self.fast = fast_period
        self.slow = slow_period

    def should_buy(self, df: pd.DataFrame, i: int) -> bool:
        if i < self.slow + 1:
            return False
        close = df["Close"]
        fast_now = calculate_sma(close.iloc[:i+1], self.fast)
        slow_now = calculate_sma(close.iloc[:i+1], self.slow)
        fast_prev = calculate_sma(close.iloc[:i], self.fast)
        slow_prev = calculate_sma(close.iloc[:i], self.slow)
        return fast_prev <= slow_prev and fast_now > slow_now

    def should_sell(self, df: pd.DataFrame, i: int, entry_price: float) -> bool:
        if i < self.slow + 1:
            return False
        close = df["Close"]
        fast_now = calculate_sma(close.iloc[:i+1], self.fast)
        slow_now = calculate_sma(close.iloc[:i+1], self.slow)
        fast_prev = calculate_sma(close.iloc[:i], self.fast)
        slow_prev = calculate_sma(close.iloc[:i], self.slow)
        return fast_prev >= slow_prev and fast_now < slow_now


class RSIStrategy(BaseStrategy):
    """Buy on RSI oversold, sell on RSI overbought."""
    name = "rsi"

    def __init__(self, oversold: float = 30, overbought: float = 70):
        self.oversold = oversold
        self.overbought = overbought

    def should_buy(self, df: pd.DataFrame, i: int) -> bool:
        if i < 15:
            return False
        rsi = calculate_rsi(df["Close"].iloc[:i+1])
        rsi_prev = calculate_rsi(df["Close"].iloc[:i])
        return rsi_prev <= self.oversold and rsi > self.oversold

    def should_sell(self, df: pd.DataFrame, i: int, entry_price: float) -> bool:
        if i < 15:
            return False
        rsi = calculate_rsi(df["Close"].iloc[:i+1])
        return rsi > self.overbought


class MACDStrategy(BaseStrategy):
    """Buy on MACD bullish crossover, sell on bearish crossover."""
    name = "macd"

    def should_buy(self, df: pd.DataFrame, i: int) -> bool:
        if i < 35:
            return False
        macd_now, sig_now, _ = calculate_macd(df["Close"].iloc[:i+1])
        macd_prev, sig_prev, _ = calculate_macd(df["Close"].iloc[:i])
        return macd_prev <= sig_prev and macd_now > sig_now

    def should_sell(self, df: pd.DataFrame, i: int, entry_price: float) -> bool:
        if i < 35:
            return False
        macd_now, sig_now, _ = calculate_macd(df["Close"].iloc[:i+1])
        macd_prev, sig_prev, _ = calculate_macd(df["Close"].iloc[:i])
        return macd_prev >= sig_prev and macd_now < sig_now


class BollingerBandStrategy(BaseStrategy):
    """Buy at lower band touch, sell at upper band touch (mean reversion)."""
    name = "bollinger"

    def should_buy(self, df: pd.DataFrame, i: int) -> bool:
        if i < 21:
            return False
        close = df["Close"].iloc[:i+1]
        upper, middle, lower = calculate_bollinger_bands(close)
        return float(close.iloc[-1]) <= lower

    def should_sell(self, df: pd.DataFrame, i: int, entry_price: float) -> bool:
        if i < 21:
            return False
        close = df["Close"].iloc[:i+1]
        upper, middle, lower = calculate_bollinger_bands(close)
        current = float(close.iloc[-1])
        return current >= upper or current >= middle


STRATEGIES = {
    "sma_crossover": SMAcrossoverStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger": BollingerBandStrategy,
}


def _calculate_sharpe(returns: pd.Series, risk_free: float = 0.05) -> float:
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    excess = returns - (risk_free / 252)
    return float(round((excess.mean() / excess.std()) * (252 ** 0.5), 3))


def _calculate_max_drawdown(equity: List[float]) -> tuple:
    if not equity:
        return 0.0, 0.0
    peak = equity[0]
    max_dd = 0.0
    for val in equity:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    peak_val = max(equity)
    trough_val = min(equity[equity.index(peak_val):]) if peak_val in equity else min(equity)
    return round(peak_val - trough_val, 2), round(max_dd * 100, 2)


def run_backtest(
    symbol: str,
    strategy_name: str = "sma_crossover",
    start_date: str = "2022-01-01",
    end_date: Optional[str] = None,
    initial_capital: float = 10000.0,
    strategy_params: Optional[dict] = None,
) -> BacktestResult:
    """
    Run a backtest for a symbol using the specified strategy.

    Args:
        symbol: Stock ticker
        strategy_name: One of sma_crossover, rsi, macd, bollinger
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (defaults to today)
        initial_capital: Starting portfolio value
        strategy_params: Optional dict of strategy parameters

    Returns:
        BacktestResult with full metrics and equity curve
    """
    if end_date is None:
        end_date = date.today().isoformat()

    if strategy_name not in STRATEGIES:
        return BacktestResult(
            symbol=symbol, strategy=strategy_name,
            start_date=start_date, end_date=end_date,
            initial_capital=initial_capital, final_value=initial_capital,
            total_return=0, total_return_pct=0, sharpe_ratio=0,
            max_drawdown=0, max_drawdown_pct=0, win_rate=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            best_trade_pct=0, worst_trade_pct=0,
            error=f"Unknown strategy: {strategy_name}"
        )

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval="1d")

        if df is None or len(df) < 30:
            return BacktestResult(
                symbol=symbol, strategy=strategy_name,
                start_date=start_date, end_date=end_date,
                initial_capital=initial_capital, final_value=initial_capital,
                total_return=0, total_return_pct=0, sharpe_ratio=0,
                max_drawdown=0, max_drawdown_pct=0, win_rate=0,
                total_trades=0, winning_trades=0, losing_trades=0,
                best_trade_pct=0, worst_trade_pct=0,
                error="Insufficient historical data"
            )

        df.index = pd.to_datetime(df.index)
        StrategyClass = STRATEGIES[strategy_name]
        params = strategy_params or {}
        strategy = StrategyClass(**params)

        commission_rate = settings.COMMISSION_RATE
        capital = initial_capital
        position = 0.0
        entry_price = 0.0
        equity_curve = []
        trades = []
        trade_pnls = []

        for i in range(len(df)):
            price = float(df["Close"].iloc[i])
            dt = df.index[i].strftime("%Y-%m-%d")
            portfolio_value = capital + (position * price)
            equity_curve.append({"date": dt, "value": round(portfolio_value, 2)})

            if position == 0 and strategy.should_buy(df, i):
                # Buy as many shares as possible
                cost_per_share = price * (1 + commission_rate)
                shares = capital / cost_per_share
                if shares > 0.01:
                    commission = shares * price * commission_rate
                    capital -= (shares * price + commission)
                    position = shares
                    entry_price = price
                    trades.append({
                        "date": dt, "action": "BUY",
                        "price": round(price, 2),
                        "quantity": round(shares, 4),
                        "value": round(shares * price, 2),
                        "pnl": 0.0
                    })

            elif position > 0 and strategy.should_sell(df, i, entry_price):
                # Sell entire position
                commission = position * price * commission_rate
                proceeds = position * price - commission
                pnl = proceeds - (position * entry_price)
                pnl_pct = (pnl / (position * entry_price)) * 100 if entry_price > 0 else 0
                capital += proceeds
                trade_pnls.append(pnl_pct)
                trades.append({
                    "date": dt, "action": "SELL",
                    "price": round(price, 2),
                    "quantity": round(position, 4),
                    "value": round(proceeds, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2)
                })
                position = 0.0

        # Close any open position at last price
        if position > 0:
            last_price = float(df["Close"].iloc[-1])
            commission = position * last_price * commission_rate
            proceeds = position * last_price - commission
            pnl = proceeds - (position * entry_price)
            pnl_pct = (pnl / (position * entry_price)) * 100 if entry_price > 0 else 0
            capital += proceeds
            trade_pnls.append(pnl_pct)
            trades.append({
                "date": df.index[-1].strftime("%Y-%m-%d"),
                "action": "SELL (Close)",
                "price": round(last_price, 2),
                "quantity": round(position, 4),
                "value": round(proceeds, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })

        final_value = capital
        total_return = final_value - initial_capital
        total_return_pct = (total_return / initial_capital) * 100

        equity_values = [e["value"] for e in equity_curve]
        max_dd_abs, max_dd_pct = _calculate_max_drawdown(equity_values)

        returns_series = pd.Series(equity_values).pct_change().dropna()
        sharpe = _calculate_sharpe(returns_series)

        wins = [p for p in trade_pnls if p > 0]
        losses = [p for p in trade_pnls if p <= 0]
        win_rate = (len(wins) / len(trade_pnls) * 100) if trade_pnls else 0

        return BacktestResult(
            symbol=symbol,
            strategy=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=round(final_value, 2),
            total_return=round(total_return, 2),
            total_return_pct=round(total_return_pct, 2),
            sharpe_ratio=sharpe,
            max_drawdown=max_dd_abs,
            max_drawdown_pct=max_dd_pct,
            win_rate=round(win_rate, 1),
            total_trades=len(trade_pnls),
            winning_trades=len(wins),
            losing_trades=len(losses),
            best_trade_pct=round(max(trade_pnls), 2) if trade_pnls else 0,
            worst_trade_pct=round(min(trade_pnls), 2) if trade_pnls else 0,
            equity_curve=equity_curve,
            trades=trades,
        )

    except Exception as e:
        logger.error(f"Backtest error for {symbol}: {e}", exc_info=True)
        return BacktestResult(
            symbol=symbol, strategy=strategy_name,
            start_date=start_date, end_date=end_date,
            initial_capital=initial_capital, final_value=initial_capital,
            total_return=0, total_return_pct=0, sharpe_ratio=0,
            max_drawdown=0, max_drawdown_pct=0, win_rate=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            best_trade_pct=0, worst_trade_pct=0,
            error=str(e)
        )
