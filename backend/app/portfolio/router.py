"""
Portfolio router: holdings, history, transactions, analytics, summary, and reset.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import get_current_active_user
from app.portfolio import service as portfolio_service
from app.portfolio.schemas import (
    PortfolioAnalytics,
    PortfolioHistoryPoint,
    PortfolioResponse,
    PortfolioSummary,
    TransactionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Portfolio"])


@router.get(
    "",
    response_model=PortfolioResponse,
    summary="Get all holdings with live prices and portfolio summary",
)
async def get_portfolio(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PortfolioResponse:
    """Return all current holdings enriched with live market data."""
    return await portfolio_service.get_portfolio(db, redis, current_user)


@router.get(
    "/summary",
    response_model=PortfolioSummary,
    summary="Get quick portfolio summary statistics",
)
async def get_summary(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PortfolioSummary:
    """Return a lightweight summary card: total value, P&L, number of positions."""
    result = await portfolio_service.get_portfolio(db, redis, current_user)
    return result.summary


@router.get(
    "/stats",
    summary="Alias for summary statistics",
)
async def get_stats(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Frontend-compatible stats alias — returns same data as /summary."""
    result = await portfolio_service.get_portfolio(db, redis, current_user)
    return result.summary


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Get portfolio value over time",
)
async def get_portfolio_history(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> List[Dict[str, Any]]:
    """Return a daily series of portfolio value, cash, and invested amounts."""
    history = await portfolio_service.get_portfolio_history(db, redis, current_user.id)
    if not history:
        # Return a single day point for brand-new users
        return [{
            "date": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d"),
            "value": float(current_user.balance),
            "cash": float(current_user.balance),
            "invested": 0.0,
        }]
    return history


@router.get(
    "/transactions",
    response_model=List[TransactionResponse],
    summary="Get transaction ledger history",
)
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[TransactionResponse]:
    """Return paginated transaction history (buys, sells, deposits, withdrawals)."""
    return await portfolio_service.get_transactions(
        db, current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/analytics",
    response_model=PortfolioAnalytics,
    summary="Get comprehensive portfolio analytics",
)
async def get_analytics(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PortfolioAnalytics:
    """
    Return full analytics: Sharpe ratio, beta, alpha, max drawdown,
    volatility, win rate, sector allocation, top/worst performers.
    """
    return await portfolio_service.get_analytics(db, redis, current_user.id, current_user)


@router.post(
    "/reset",
    summary="Reset portfolio to initial state",
)
async def reset_portfolio(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """
    Reset the authenticated user's portfolio:
    - Delete all holdings
    - Delete all transactions
    - Reset balance to starting amount
    - Clear portfolio cache
    """
    from app.portfolio.models import Holding, Transaction
    from app.core.redis_client import delete_pattern

    # Delete all holdings
    await db.execute(delete(Holding).where(Holding.user_id == current_user.id))

    # Delete all transactions
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))

    # Reset balance
    current_user.balance = Decimal(str(settings.STARTING_BALANCE))
    db.add(current_user)
    await db.flush()

    # Clear Redis cache for this user
    if redis:
        await delete_pattern(redis, f"portfolio:{current_user.id}*")
        await delete_pattern(redis, f"analytics:{current_user.id}*")

    logger.info("Portfolio reset for user %s", current_user.username)
    return {
        "message": "Portfolio reset successfully.",
        "new_balance": float(settings.STARTING_BALANCE),
    }
