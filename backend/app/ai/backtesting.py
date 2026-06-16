"""
Backtesting engine: replay trading strategies against historical data.
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

import pandas as pd
import yfinance as yf

from app.ai.indicators import calculate_rsi, calculate_macd, calculate_sma, calculate_bollinger_bands
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    symbol: str; strategy: str; start_date: str; end_date: str
    initial_capital: float; final_value: float; total_return: float; total_return_pct: float
    sharpe_ratio: float; max_drawdown: float; max_drawdown_pct: float
    win_rate: float; total_trades: int; winning_trades: int; losing_trades: int
    best_trade_pct: float; worst_trade_pct: float
    equity_curve: List[dict] = field(default_factory=list)
    trades: List[dict] = field(default_factory=list)
    error: Optional[str] = None


class BaseStrategy:
    name = "base"
    def should_buy(self, df: pd.DataFrame, i: int) -> bool: raise NotImplementedError
    def should_sell(self, df: pd.DataFrame, i: int, entry_price: float) -> bool: raise NotImplementedError


class SMAcrossoverStrategy(BaseStrategy):
    name = "sma_crossover"
    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        self.fast, self.slow = fast_period, slow_period
    def should_buy(self, df, i):
        if i < self.slow + 1: return False
        c = df["Close"]
        return calculate_sma(c.iloc[:i], self.fast) <= calculate_sma(c.iloc[:i], self.slow) and calculate_sma(c.iloc[:i+1], self.fast) > calculate_sma(c.iloc[:i+1], self.slow)
    def should_sell(self, df, i, entry_price):
        if i < self.slow + 1: return False
        c = df["Close"]
        return calculate_sma(c.iloc[:i], self.fast) >= calculate_sma(c.iloc[:i], self.slow) and calculate_sma(c.iloc[:i+1], self.fast) < calculate_sma(c.iloc[:i+1], self.slow)


class RSIStrategy(BaseStrategy):
    name = "rsi"
    def __init__(self, oversold: float = 30, overbought: float = 70):
        self.oversold, self.overbought = oversold, overbought
    def should_buy(self, df, i):
        if i < 15: return False
        return calculate_rsi(df["Close"].iloc[:i]) <= self.oversold and calculate_rsi(df["Close"].iloc[:i+1]) > self.oversold
    def should_sell(self, df, i, entry_price):
        if i < 15: return False
        return calculate_rsi(df["Close"].iloc[:i+1]) > self.overbought


class MACDStrategy(BaseStrategy):
    name = "macd"
    def should_buy(self, df, i):
        if i < 35: return False
        ml_now, sl_now, _ = calculate_macd(df["Close"].iloc[:i+1])
        ml_prev, sl_prev, _ = calculate_macd(df["Close"].iloc[:i])
        return ml_prev <= sl_prev and ml_now > sl_now
    def should_sell(self, df, i, entry_price):
        if i < 35: return False
        ml_now, sl_now, _ = calculate_macd(df["Close"].iloc[:i+1])
        ml_prev, sl_prev, _ = calculate_macd(df["Close"].iloc[:i])
        return ml_prev >= sl_prev and ml_now < sl_now


class BollingerBandStrategy(BaseStrategy):
    name = "bollinger"
    def should_buy(self, df, i):
        if i < 21: return False
        _, _, lower = calculate_bollinger_bands(df["Close"].iloc[:i+1])
        return float(df["Close"].iloc[i]) <= lower
    def should_sell(self, df, i, entry_price):
        if i < 21: return False
        upper, middle, _ = calculate_bollinger_bands(df["Close"].iloc[:i+1])
        current = float(df["Close"].iloc[i])
        return current >= upper or current >= middle


STRATEGIES = {"sma_crossover": SMAcrossoverStrategy, "rsi": RSIStrategy, "macd": MACDStrategy, "bollinger": BollingerBandStrategy}


def run_backtest(symbol: str, strategy_name: str = "sma_crossover", start_date: str = "2022-01-01", end_date: Optional[str] = None, initial_capital: float = 10000.0, strategy_params: Optional[dict] = None) -> BacktestResult:
    if end_date is None:
        end_date = date.today().isoformat()
    empty = BacktestResult(symbol=symbol, strategy=strategy_name, start_date=start_date, end_date=end_date, initial_capital=initial_capital, final_value=initial_capital, total_return=0, total_return_pct=0, sharpe_ratio=0, max_drawdown=0, max_drawdown_pct=0, win_rate=0, total_trades=0, winning_trades=0, losing_trades=0, best_trade_pct=0, worst_trade_pct=0)
    if strategy_name not in STRATEGIES:
        empty.error = f"Unknown strategy: {strategy_name}"; return empty
    try:
        df = yf.Ticker(symbol).history(start=start_date, end=end_date, interval="1d")
        if df is None or len(df) < 30:
            empty.error = "Insufficient historical data"; return empty
        strategy = STRATEGIES[strategy_name](**(strategy_params or {}))
        commission_rate = settings.COMMISSION_RATE
        capital, position, entry_price = initial_capital, 0.0, 0.0
        equity_curve, trades, trade_pnls = [], [], []
        for i in range(len(df)):
            price = float(df["Close"].iloc[i])
            dt = df.index[i].strftime("%Y-%m-%d")
            equity_curve.append({"date": dt, "value": round(capital + position * price, 2)})
            if position == 0 and strategy.should_buy(df, i):
                shares = capital / (price * (1 + commission_rate))
                if shares > 0.01:
                    capital -= shares * price * (1 + commission_rate)
                    position, entry_price = shares, price
                    trades.append({"date": dt, "action": "BUY", "price": round(price, 2), "quantity": round(shares, 4), "value": round(shares * price, 2), "pnl": 0.0})
            elif position > 0 and strategy.should_sell(df, i, entry_price):
                proceeds = position * price * (1 - commission_rate)
                pnl_pct = ((proceeds - position * entry_price) / (position * entry_price) * 100) if entry_price > 0 else 0
                capital += proceeds
                trade_pnls.append(pnl_pct)
                trades.append({"date": dt, "action": "SELL", "price": round(price, 2), "quantity": round(position, 4), "value": round(proceeds, 2), "pnl_pct": round(pnl_pct, 2)})
                position = 0.0
        if position > 0:
            last_price = float(df["Close"].iloc[-1])
            proceeds = position * last_price * (1 - commission_rate)
            pnl_pct = ((proceeds - position * entry_price) / (position * entry_price) * 100) if entry_price > 0 else 0
            capital += proceeds; trade_pnls.append(pnl_pct)
            trades.append({"date": df.index[-1].strftime("%Y-%m-%d"), "action": "SELL (Close)", "price": round(last_price, 2), "value": round(proceeds, 2), "pnl_pct": round(pnl_pct, 2)})
        equity_vals = [e["value"] for e in equity_curve]
        peak = max(equity_vals) if equity_vals else initial_capital
        trough = min(equity_vals[equity_vals.index(peak):]) if peak in equity_vals else min(equity_vals) if equity_vals else initial_capital
        max_dd_pct = ((peak - trough) / peak * 100) if peak > 0 else 0
        returns_series = pd.Series(equity_vals).pct_change().dropna()
        sharpe = float(round(((returns_series - 0.05/252).mean() / returns_series.std()) * (252 ** 0.5), 3)) if len(returns_series) > 1 and returns_series.std() != 0 else 0.0
        wins = [p for p in trade_pnls if p > 0]
        return BacktestResult(symbol=symbol, strategy=strategy_name, start_date=start_date, end_date=end_date, initial_capital=initial_capital, final_value=round(capital, 2), total_return=round(capital - initial_capital, 2), total_return_pct=round((capital - initial_capital) / initial_capital * 100, 2), sharpe_ratio=sharpe, max_drawdown=round(peak - trough, 2), max_drawdown_pct=round(max_dd_pct, 2), win_rate=round(len(wins) / len(trade_pnls) * 100, 1) if trade_pnls else 0, total_trades=len(trade_pnls), winning_trades=len(wins), losing_trades=len(trade_pnls) - len(wins), best_trade_pct=round(max(trade_pnls), 2) if trade_pnls else 0, worst_trade_pct=round(min(trade_pnls), 2) if trade_pnls else 0, equity_curve=equity_curve, trades=trades)
    except Exception as e:
        logger.error(f"Backtest error for {symbol}: {e}", exc_info=True)
        empty.error = str(e); return empty
