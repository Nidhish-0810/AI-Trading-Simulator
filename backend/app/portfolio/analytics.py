"""
Portfolio analytics: Sharpe ratio, beta, alpha, max drawdown, volatility,
win rate, sector allocation, and portfolio value history.

All functions accept pandas Series/DataFrames and return float values or dicts.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE_DAILY = 0.05 / TRADING_DAYS_PER_YEAR  # 5 % annualised


# ── Core metrics ───────────────────────────────────────────────────────────────
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05,
) -> Optional[float]:
    """
    Compute the annualised Sharpe ratio.

    Args:
        returns: Daily return series (decimal, not percentage).
        risk_free_rate: Annual risk-free rate (default 5 %).

    Returns:
        Annualised Sharpe ratio, or None if insufficient data.
    """
    if returns is None or len(returns) < 5:
        return None
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    std = excess.std()
    if std == 0:
        return None
    sharpe = (excess.mean() / std) * np.sqrt(TRADING_DAYS_PER_YEAR)
    return round(float(sharpe), 4)


def calculate_beta(
    portfolio_returns: pd.Series,
    market_returns: pd.Series,
) -> Optional[float]:
    """
    Calculate portfolio beta relative to the market (S&P 500).

    Args:
        portfolio_returns: Daily returns of the portfolio.
        market_returns: Daily returns of the benchmark (e.g., SPY).

    Returns:
        Beta coefficient, or None if insufficient data.
    """
    if portfolio_returns is None or market_returns is None:
        return None
    combined = pd.concat(
        [portfolio_returns, market_returns], axis=1, join="inner"
    ).dropna()
    if len(combined) < 5:
        return None
    p = combined.iloc[:, 0]
    m = combined.iloc[:, 1]
    cov = np.cov(p, m)
    market_var = cov[1, 1]
    if market_var == 0:
        return None
    beta = cov[0, 1] / market_var
    return round(float(beta), 4)


def calculate_alpha(
    portfolio_returns: pd.Series,
    market_returns: pd.Series,
    risk_free_rate: float = 0.05,
) -> Optional[float]:
    """
    Calculate Jensen's Alpha (annualised).

    alpha = R_p - [R_f + beta * (R_m - R_f)]
    """
    beta = calculate_beta(portfolio_returns, market_returns)
    if beta is None:
        return None

    combined = pd.concat(
        [portfolio_returns, market_returns], axis=1, join="inner"
    ).dropna()
    if len(combined) < 5:
        return None

    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    avg_p = combined.iloc[:, 0].mean()
    avg_m = combined.iloc[:, 1].mean()

    alpha_daily = avg_p - (daily_rf + beta * (avg_m - daily_rf))
    alpha_annual = alpha_daily * TRADING_DAYS_PER_YEAR
    return round(float(alpha_annual), 4)


def calculate_max_drawdown(portfolio_values: pd.Series) -> Optional[float]:
    """
    Calculate the maximum peak-to-trough drawdown.

    Returns:
        Max drawdown as a negative percentage (e.g., -0.25 = -25%), or None.
    """
    if portfolio_values is None or len(portfolio_values) < 2:
        return None
    roll_max = portfolio_values.cummax()
    drawdown = (portfolio_values - roll_max) / roll_max
    max_dd = drawdown.min()
    return round(float(max_dd) * 100, 4)


def calculate_win_rate(trades: list) -> float:
    """
    Calculate the percentage of sell trades that were profitable.

    A trade is considered profitable if its executed_price exceeds the
    average_cost of the holding at time of sale. Since average_cost is
    not directly on the Trade model, we approximate using total_value
    vs commission as a proxy.

    Args:
        trades: List of Trade ORM objects.

    Returns:
        Win rate as a percentage (0-100).
    """
    sell_trades = [t for t in trades if t.side == "sell"]
    if not sell_trades:
        return 0.0
    # A trade is profitable if the net proceeds > cost
    # Without historical cost data here we compare executed_price presence
    wins = sum(
        1
        for t in sell_trades
        if float(t.total_value) - float(t.commission) > 0
    )
    return round(wins / len(sell_trades) * 100, 2)


def calculate_volatility(returns: pd.Series) -> Optional[float]:
    """
    Calculate the annualised standard deviation of returns.

    Returns:
        Annualised volatility as a percentage, or None if insufficient data.
    """
    if returns is None or len(returns) < 5:
        return None
    vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    return round(float(vol) * 100, 4)  # as %


# ── Sector allocation ──────────────────────────────────────────────────────────
def get_sector_allocation(
    holdings_with_value: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Map holdings to sectors and return percentage allocation.

    Args:
        holdings_with_value: List of dicts with 'symbol', 'current_value', 'sector'.

    Returns:
        Dict mapping sector name -> % of total portfolio.
    """
    from app.market.yfinance_client import STOCK_LOOKUP

    sector_totals: Dict[str, float] = {}
    total_value = sum(h.get("current_value", 0) or 0 for h in holdings_with_value)

    if total_value == 0:
        return {}

    for h in holdings_with_value:
        symbol = h.get("symbol", "")
        value = h.get("current_value") or 0
        meta = STOCK_LOOKUP.get(symbol, {})
        sector = meta.get("sector", "Other")
        sector_totals[sector] = sector_totals.get(sector, 0) + value

    allocation = {
        sector: round(value / total_value * 100, 2)
        for sector, value in sector_totals.items()
    }
    return allocation


# ── Portfolio history ──────────────────────────────────────────────────────────
async def calculate_portfolio_history(
    db, user_id
) -> List[Dict[str, Any]]:
    """
    Build a daily portfolio value time series from transaction history.

    Uses a simple running balance: starting cash minus cumulative buy spend
    plus cumulative sell proceeds, adjusted at each transaction date.

    Returns:
        List of {date, value, cash, invested} dicts ordered by date.
    """
    from sqlalchemy import select
    from app.portfolio.models import Transaction
    from app.core.config import settings

    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.asc())
    )
    txns = result.scalars().all()

    if not txns:
        return []

    # Build a day-by-day series
    start_date = txns[0].created_at.date()
    end_date = datetime.utcnow().date()
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    running_cash = float(settings.STARTING_BALANCE)
    running_invested = 0.0
    txn_idx = 0
    history = []

    for date in dates:
        date_obj = date.date()
        while txn_idx < len(txns) and txns[txn_idx].created_at.date() <= date_obj:
            t = txns[txn_idx]
            if t.type == "buy":
                running_cash -= float(t.total_amount)
                running_invested += float(t.total_amount)
            elif t.type == "sell":
                running_cash += float(t.total_amount)
                running_invested -= float(t.total_amount)
            txn_idx += 1

        portfolio_value = running_cash + running_invested
        history.append(
            {
                "date": str(date_obj),
                "value": round(portfolio_value, 2),
                "cash": round(running_cash, 2),
                "invested": round(running_invested, 2),
            }
        )

    return history


# ── Support / Resistance ───────────────────────────────────────────────────────
def detect_support_resistance(
    history_df: pd.DataFrame,
    window: int = 20,
) -> Tuple[float, float]:
    """
    Detect the primary support and resistance levels using rolling min/max.

    Args:
        history_df: DataFrame with at minimum a 'close' column.
        window: Rolling window size in bars.

    Returns:
        Tuple of (support, resistance) prices.
    """
    if history_df is None or len(history_df) < window:
        close = history_df["close"] if history_df is not None and len(history_df) > 0 else pd.Series([0])
        return float(close.min()), float(close.max())

    close = history_df["close"]
    rolling_min = close.rolling(window=window).min()
    rolling_max = close.rolling(window=window).max()

    support = float(rolling_min.dropna().iloc[-1]) if not rolling_min.dropna().empty else float(close.min())
    resistance = float(rolling_max.dropna().iloc[-1]) if not rolling_max.dropna().empty else float(close.max())
    return round(support, 4), round(resistance, 4)
