"""
Portfolio analytics: Sharpe, beta, alpha, max drawdown, volatility, win rate.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
TRADING_DAYS_PER_YEAR = 252


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05) -> Optional[float]:
    if returns is None or len(returns) < 5:
        return None
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess = returns - daily_rf
    std = excess.std()
    if std == 0:
        return None
    return round(float((excess.mean() / std) * np.sqrt(TRADING_DAYS_PER_YEAR)), 4)


def calculate_beta(portfolio_returns: pd.Series, market_returns: pd.Series) -> Optional[float]:
    if portfolio_returns is None or market_returns is None:
        return None
    combined = pd.concat([portfolio_returns, market_returns], axis=1, join="inner").dropna()
    if len(combined) < 5:
        return None
    cov = np.cov(combined.iloc[:, 0], combined.iloc[:, 1])
    market_var = cov[1, 1]
    if market_var == 0:
        return None
    return round(float(cov[0, 1] / market_var), 4)


def calculate_alpha(portfolio_returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.05) -> Optional[float]:
    beta = calculate_beta(portfolio_returns, market_returns)
    if beta is None:
        return None
    combined = pd.concat([portfolio_returns, market_returns], axis=1, join="inner").dropna()
    if len(combined) < 5:
        return None
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    alpha_daily = combined.iloc[:, 0].mean() - (daily_rf + beta * (combined.iloc[:, 1].mean() - daily_rf))
    return round(float(alpha_daily * TRADING_DAYS_PER_YEAR), 4)


def calculate_max_drawdown(portfolio_values: pd.Series) -> Optional[float]:
    if portfolio_values is None or len(portfolio_values) < 2:
        return None
    roll_max = portfolio_values.cummax()
    drawdown = (portfolio_values - roll_max) / roll_max
    return round(float(drawdown.min()) * 100, 4)


def calculate_win_rate(trades: list) -> float:
    sell_trades = [t for t in trades if t.side == "sell"]
    if not sell_trades:
        return 0.0
    wins = sum(1 for t in sell_trades if float(t.total_value) - float(t.commission) > 0)
    return round(wins / len(sell_trades) * 100, 2)


def calculate_volatility(returns: pd.Series) -> Optional[float]:
    if returns is None or len(returns) < 5:
        return None
    return round(float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) * 100, 4)


def get_sector_allocation(holdings_with_value: List[Dict[str, Any]]) -> Dict[str, float]:
    from app.market.yfinance_client import STOCK_LOOKUP
    sector_totals: Dict[str, float] = {}
    total_value = sum(h.get("current_value", 0) or 0 for h in holdings_with_value)
    if total_value == 0:
        return {}
    for h in holdings_with_value:
        sector = STOCK_LOOKUP.get(h.get("symbol", ""), {}).get("sector", "Other")
        sector_totals[sector] = sector_totals.get(sector, 0) + (h.get("current_value") or 0)
    return {s: round(v / total_value * 100, 2) for s, v in sector_totals.items()}


async def calculate_portfolio_history(db, user_id) -> List[Dict[str, Any]]:
    from sqlalchemy import select
    from app.portfolio.models import Transaction
    from app.core.config import settings
    result = await db.execute(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created_at.asc()))
    txns = result.scalars().all()
    if not txns:
        return []
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
            if t.transaction_type == "buy":
                running_cash -= float(t.total_amount)
                running_invested += float(t.total_amount)
            elif t.transaction_type == "sell":
                running_cash += float(t.total_amount)
                running_invested -= float(t.total_amount)
            txn_idx += 1
        history.append({"date": str(date_obj), "value": round(running_cash + running_invested, 2), "cash": round(running_cash, 2), "invested": round(running_invested, 2)})
    return history


def detect_support_resistance(history_df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    if history_df is None or len(history_df) < window:
        close = history_df["Close"] if history_df is not None and len(history_df) > 0 else pd.Series([0])
        return float(close.min()), float(close.max())
    close = history_df["Close"]
    support = float(close.rolling(window=window).min().dropna().iloc[-1]) if not close.rolling(window=window).min().dropna().empty else float(close.min())
    resistance = float(close.rolling(window=window).max().dropna().iloc[-1]) if not close.rolling(window=window).max().dropna().empty else float(close.max())
    return round(support, 4), round(resistance, 4)
