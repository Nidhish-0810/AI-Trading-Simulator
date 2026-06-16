"""
Portfolio router: holdings, history, transactions, analytics, summary, reset.
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import get_redis, delete_pattern
from app.core.security import get_current_active_user
from app.portfolio import service as portfolio_service
from app.portfolio.schemas import PortfolioAnalytics, PortfolioResponse, PortfolioSummary, TransactionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> PortfolioResponse:
    return await portfolio_service.get_portfolio(db, redis, current_user)


@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> PortfolioSummary:
    result = await portfolio_service.get_portfolio(db, redis, current_user)
    return result.summary


@router.get("/stats")
async def get_stats(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    result = await portfolio_service.get_portfolio(db, redis, current_user)
    return result.summary


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_portfolio_history(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> List[Dict[str, Any]]:
    import datetime
    history = await portfolio_service.get_portfolio_history(db, redis, current_user.id)
    if not history:
        return [{"date": datetime.datetime.utcnow().strftime("%Y-%m-%d"), "value": float(current_user.balance), "cash": float(current_user.balance), "invested": 0.0}]
    return history


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> List[TransactionResponse]:
    return await portfolio_service.get_transactions(db, current_user.id, skip=skip, limit=limit)


@router.get("/analytics", response_model=PortfolioAnalytics)
async def get_analytics(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> PortfolioAnalytics:
    return await portfolio_service.get_analytics(db, redis, current_user.id, current_user)


@router.post("/reset")
async def reset_portfolio(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> Dict[str, Any]:
    from app.portfolio.models import Holding, Transaction
    await db.execute(delete(Holding).where(Holding.user_id == current_user.id))
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    current_user.balance = Decimal(str(settings.STARTING_BALANCE))
    await db.flush()
    if redis:
        await delete_pattern(redis, f"portfolio:{current_user.id}*")
        await delete_pattern(redis, f"analytics:{current_user.id}*")
    return {"message": "Portfolio reset successfully.", "new_balance": float(settings.STARTING_BALANCE)}
