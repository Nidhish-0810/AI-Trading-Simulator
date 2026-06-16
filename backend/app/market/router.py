"""
Market data router: quotes, history, news, search, indices, watchlist.
"""
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import get_current_active_user
from app.market import service as mkt_service
from app.market.schemas import MarketSummary, NewsItem, StockHistory, StockQuote, StockSearch, WatchlistItemResponse
from app.trading.models import WatchlistItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["Market Data"])
_SYMBOL_RE = re.compile(r"^[A-Z0-9\-\^\.]{1,10}$")


def _validate_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if not _SYMBOL_RE.match(s):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid symbol: '{symbol}'")
    return s


@router.get("/stocks", response_model=Dict[str, Any])
async def list_stocks(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                     search: Optional[str] = Query(None), sector: Optional[str] = Query(None)) -> Dict[str, Any]:
    return mkt_service.get_all_stocks(page=page, page_size=page_size, search=search, sector=sector)


@router.get("/stock/{symbol}", response_model=StockQuote)
async def get_stock(symbol: str, redis=Depends(get_redis)) -> StockQuote:
    quote = await mkt_service.fetch_quote(_validate_symbol(symbol), redis)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found.")
    return quote


@router.get("/quote/{symbol}", response_model=StockQuote)
async def get_quote_alias(symbol: str, redis=Depends(get_redis)) -> StockQuote:
    quote = await mkt_service.fetch_quote(_validate_symbol(symbol), redis)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found.")
    return quote


@router.post("/quotes", response_model=Dict[str, Any])
async def get_batch_quotes(body: Dict[str, Any], redis=Depends(get_redis)) -> Dict[str, Any]:
    symbols = body.get("symbols", [])
    if not symbols or len(symbols) > 50:
        raise HTTPException(status_code=400, detail="1-50 symbols required.")
    validated = [_validate_symbol(s) for s in symbols]
    quotes = await mkt_service.fetch_multiple_quotes(validated, redis)
    return {sym: q.model_dump() for sym, q in quotes.items()}


@router.get("/stock/{symbol}/history", response_model=StockHistory)
async def get_history(symbol: str, period: str = Query("1y"), interval: str = Query("1d"), redis=Depends(get_redis)) -> StockHistory:
    history = await mkt_service.fetch_history(_validate_symbol(symbol), period=period, interval=interval, redis=redis)
    if history is None:
        raise HTTPException(status_code=404, detail=f"History for '{symbol}' not found.")
    return history


@router.get("/history/{symbol}", response_model=StockHistory)
async def get_history_alias(symbol: str, interval: str = Query("1D"), range: str = Query("3M"), redis=Depends(get_redis)) -> StockHistory:
    period_map = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "MAX": "max"}
    interval_map = {"1D": "1d", "1W": "1wk", "1M": "1mo", "1H": "1h", "15M": "15m", "5M": "5m"}
    history = await mkt_service.fetch_history(_validate_symbol(symbol), period=period_map.get(range.upper(), "3mo"), interval=interval_map.get(interval.upper(), "1d"), redis=redis)
    if history is None:
        raise HTTPException(status_code=404, detail=f"History for '{symbol}' not found.")
    return history


@router.get("/stock/{symbol}/news", response_model=List[NewsItem])
async def get_news(symbol: str, redis=Depends(get_redis)) -> List[NewsItem]:
    return await mkt_service.fetch_news(_validate_symbol(symbol), redis)


@router.get("/news/{symbol}", response_model=List[NewsItem])
async def get_news_alias(symbol: str, limit: int = Query(10, ge=1, le=50), redis=Depends(get_redis)) -> List[NewsItem]:
    news = await mkt_service.fetch_news(_validate_symbol(symbol), redis)
    return news[:limit]


@router.get("/search", response_model=List[StockSearch])
async def search(q: str = Query(..., min_length=1)) -> List[StockSearch]:
    from app.market.yfinance_client import search_stocks
    return search_stocks(q)


@router.get("/summary", response_model=MarketSummary)
async def market_summary(redis=Depends(get_redis)) -> MarketSummary:
    return await mkt_service.fetch_market_summary(redis)


@router.get("/trending", response_model=List[StockQuote])
async def trending(redis=Depends(get_redis)) -> List[StockQuote]:
    return await mkt_service.fetch_trending(redis)


@router.get("/gainers", response_model=List[StockQuote])
async def top_gainers(limit: int = Query(10, ge=1, le=50), redis=Depends(get_redis)) -> List[StockQuote]:
    return await mkt_service.fetch_movers("gainers", limit, redis)


@router.get("/losers", response_model=List[StockQuote])
async def top_losers(limit: int = Query(10, ge=1, le=50), redis=Depends(get_redis)) -> List[StockQuote]:
    return await mkt_service.fetch_movers("losers", limit, redis)


@router.get("/active", response_model=List[StockQuote])
async def most_active(limit: int = Query(10, ge=1, le=50), redis=Depends(get_redis)) -> List[StockQuote]:
    return await mkt_service.fetch_movers("active", limit, redis)


@router.get("/watchlist", response_model=List[WatchlistItemResponse])
async def get_watchlist(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)) -> List[WatchlistItemResponse]:
    result = await db.execute(select(WatchlistItem).where(WatchlistItem.user_id == current_user.id).order_by(WatchlistItem.added_at.desc()))
    items = result.scalars().all()
    if not items:
        return []
    quotes_dict = await mkt_service.fetch_multiple_quotes([item.symbol for item in items], redis)
    return [WatchlistItemResponse(symbol=item.symbol, added_at=item.added_at, quote=quotes_dict.get(item.symbol)) for item in items]


@router.post("/watchlist/{symbol}", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(symbol: str, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    symbol = _validate_symbol(symbol)
    existing = await db.execute(select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.symbol == symbol))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"'{symbol}' already in watchlist.")
    db.add(WatchlistItem(id=uuid.uuid4(), user_id=current_user.id, symbol=symbol))
    await db.flush()
    return {"message": f"'{symbol}' added to watchlist."}


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist_body(body: Dict[str, str], current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    symbol = _validate_symbol(body.get("symbol", ""))
    existing = await db.execute(select(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.symbol == symbol))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"'{symbol}' already in watchlist.")
    db.add(WatchlistItem(id=uuid.uuid4(), user_id=current_user.id, symbol=symbol))
    await db.flush()
    return {"message": f"'{symbol}' added to watchlist."}


@router.delete("/watchlist/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(symbol: str, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> None:
    symbol = _validate_symbol(symbol)
    result = await db.execute(delete(WatchlistItem).where(WatchlistItem.user_id == current_user.id, WatchlistItem.symbol == symbol))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"'{symbol}' not found in watchlist.")
