"""
Portfolio service: holdings with live prices, transactions, analytics, history.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache
from app.market import service as mkt_service
from app.portfolio import analytics as calc
from app.portfolio.models import Holding, Transaction
from app.portfolio.schemas import HoldingResponse, PortfolioAnalytics, PortfolioResponse, PortfolioSummary, TransactionResponse

logger = logging.getLogger(__name__)


async def get_portfolio(db: AsyncSession, redis, user) -> PortfolioResponse:
    result = await db.execute(select(Holding).where(Holding.user_id == user.id))
    holdings = result.scalars().all()
    total_cost, total_current_value, day_pnl_total = 0.0, 0.0, 0.0
    enriched: List[HoldingResponse] = []
    for h in holdings:
        qty, avg_cost = float(h.quantity), float(h.average_cost)
        cost_basis = qty * avg_cost
        total_cost += cost_basis
        quote = await mkt_service.fetch_quote(h.symbol, redis)
        if quote:
            current_price = quote.price
            current_value = qty * current_price
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0.0
            day_change = qty * quote.change
            total_current_value += current_value
            day_pnl_total += day_change
            enriched.append(HoldingResponse(id=h.id, symbol=h.symbol, quantity=qty, average_cost=avg_cost, current_price=round(current_price, 4), current_value=round(current_value, 4), total_cost=round(cost_basis, 4), pnl=round(pnl, 4), pnl_pct=round(pnl_pct, 4), day_change=round(day_change, 4), day_change_pct=round(quote.change_pct, 4)))
        else:
            enriched.append(HoldingResponse(id=h.id, symbol=h.symbol, quantity=qty, average_cost=avg_cost, current_price=avg_cost, current_value=cost_basis, total_cost=cost_basis, pnl=0.0, pnl_pct=0.0, day_change=0.0, day_change_pct=0.0))
            total_current_value += cost_basis
    cash = float(user.balance)
    total_value = cash + total_current_value
    total_pnl = total_current_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0.0
    day_pnl_pct = ((day_pnl_total / (total_current_value - day_pnl_total) * 100) if (total_current_value - day_pnl_total) != 0 else 0.0)
    summary = PortfolioSummary(cash_balance=round(cash, 4), portfolio_value=round(total_current_value, 4), total_value=round(total_value, 4), total_cost=round(total_cost, 4), total_pnl=round(total_pnl, 4), total_pnl_pct=round(total_pnl_pct, 4), day_pnl=round(day_pnl_total, 4), day_pnl_pct=round(day_pnl_pct, 4), num_positions=len(enriched))
    return PortfolioResponse(holdings=enriched, summary=summary)


async def get_transactions(db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[TransactionResponse]:
    result = await db.execute(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).offset(skip).limit(limit))
    return [TransactionResponse.model_validate(t) for t in result.scalars().all()]


async def get_portfolio_history(db: AsyncSession, redis, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    cache_key = f"portfolio:history:{user_id}"
    if redis:
        cached = await get_cache(redis, cache_key)
        if cached:
            return cached
    history = await calc.calculate_portfolio_history(db, user_id)
    if history and redis:
        await set_cache(redis, cache_key, history, ttl=300)
    return history


async def get_analytics(db: AsyncSession, redis, user_id: uuid.UUID, user) -> PortfolioAnalytics:
    from app.trading.models import Trade as TradeModel
    history = await get_portfolio_history(db, redis, user_id)
    sharpe = beta = alpha = max_dd = vol = total_return = None
    if len(history) >= 5:
        values = pd.Series([h["value"] for h in history])
        returns = values.pct_change().dropna()
        sharpe = calc.calculate_sharpe_ratio(returns)
        vol = calc.calculate_volatility(returns)
        max_dd = calc.calculate_max_drawdown(values)
        if values.iloc[0] > 0:
            total_return = round((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100, 4)
        try:
            spy_history = await mkt_service.fetch_history("SPY", period="1y", interval="1d")
            if spy_history and len(spy_history.bars) >= 5:
                spy_returns = pd.Series([b.close for b in spy_history.bars]).pct_change().dropna()
                min_len = min(len(returns), len(spy_returns))
                beta = calc.calculate_beta(returns.iloc[-min_len:], spy_returns.iloc[-min_len:])
                alpha = calc.calculate_alpha(returns.iloc[-min_len:], spy_returns.iloc[-min_len:])
        except Exception as exc:
            logger.warning("Could not compute beta/alpha: %s", exc)
    trades_result = await db.execute(select(TradeModel).where(TradeModel.user_id == user_id))
    win_rate = calc.calculate_win_rate(trades_result.scalars().all())
    holdings_result = await db.execute(select(Holding).where(Holding.user_id == user_id))
    holdings = holdings_result.scalars().all()
    holdings_with_value, enriched_for_sort = [], []
    for h in holdings:
        quote = await mkt_service.fetch_quote(h.symbol, redis)
        qty, avg_cost = float(h.quantity), float(h.average_cost)
        cost_basis = qty * avg_cost
        current_price = quote.price if quote else avg_cost
        current_value = qty * current_price
        pnl_pct = ((current_value - cost_basis) / cost_basis * 100) if cost_basis else 0.0
        from app.market.yfinance_client import STOCK_LOOKUP
        meta = STOCK_LOOKUP.get(h.symbol, {})
        holdings_with_value.append({"symbol": h.symbol, "current_value": current_value, "sector": meta.get("sector")})
        enriched_for_sort.append({"symbol": h.symbol, "pnl_pct": round(pnl_pct, 2), "current_value": round(current_value, 2)})
    sector_allocation = calc.get_sector_allocation(holdings_with_value)
    sorted_by_pnl = sorted(enriched_for_sort, key=lambda x: x["pnl_pct"], reverse=True)
    return PortfolioAnalytics(sharpe_ratio=sharpe, beta=beta, alpha=alpha, max_drawdown=max_dd, volatility=vol, win_rate=win_rate, total_return=total_return, sector_allocation=sector_allocation, top_performers=sorted_by_pnl[:5], worst_performers=sorted_by_pnl[-5:][::-1])
