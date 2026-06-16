"""
Market data router: stock quotes, history, news, search, indices, watchlist,
gainers, losers, most-active, and batch quotes.
"""

import asyncio
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
from app.market.schemas import (
    MarketSummary,
    NewsItem,
    StockHistory,
    StockQuote,
    StockSearch,
    WatchlistItemResponse,
)
from app.trading.models import WatchlistItem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Market Data"])

# Valid symbol pattern: 1-10 uppercase alphanumeric + hyphen
_SYMBOL_RE = re.compile(r"^[A-Z0-9\-\^\.]{1,10}$")


def _validate_symbol(symbol: str) -> str:
    """Normalize and validate a ticker symbol."""
    s = symbol.upper().strip()
    if not _SYMBOL_RE.match(s):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid symbol format: '{symbol}'. Must be 1-10 alphanumeric characters.",
        )
    return s


# ── Stock catalogue ────────────────────────────────────────────────────────────
@router.get(
    "/stocks",
    response_model=Dict[str, Any],
    summary="List stocks with pagination, search, and sector filter",
)
async def list_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    sector: Optional[str] = Query(None, max_length=100),
) -> Dict[str, Any]:
    """Return a paginated list of available stocks, filterable by name/sector."""
    return mkt_service.get_all_stocks(
        page=page, page_size=page_size, search=search, sector=sector
    )


# ── Single stock quote (two aliases) ──────────────────────────────────────────
async def _get_quote_response(symbol: str, redis) -> StockQuote:
    quote = await mkt_service.fetch_quote(symbol, redis)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{symbol}' not found or unavailable.",
        )
    return quote


@router.get(
    "/stock/{symbol}",
    response_model=StockQuote,
    summary="Get full real-time quote for a symbol",
)
async def get_stock(
    symbol: str,
    redis=Depends(get_redis),
) -> StockQuote:
    """Fetch a real-time quote including price, change, fundamentals."""
    return await _get_quote_response(_validate_symbol(symbol), redis)


@router.get(
    "/quote/{symbol}",
    response_model=StockQuote,
    summary="Alias: get real-time quote for a symbol",
)
async def get_quote_alias(
    symbol: str,
    redis=Depends(get_redis),
) -> StockQuote:
    """Alias of /stock/{symbol} for frontend compatibility."""
    return await _get_quote_response(_validate_symbol(symbol), redis)


# ── Batch quotes ───────────────────────────────────────────────────────────────
@router.post(
    "/quotes",
    response_model=Dict[str, Any],
    summary="Get quotes for multiple symbols at once",
)
async def get_batch_quotes(
    body: Dict[str, Any],
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """Fetch quotes for a list of symbols concurrently."""
    symbols = body.get("symbols", [])
    if not symbols or not isinstance(symbols, list):
        raise HTTPException(status_code=400, detail="'symbols' list required in body.")
    if len(symbols) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols per batch.")
    validated = [_validate_symbol(s) for s in symbols]
    quotes = await mkt_service.fetch_multiple_quotes(validated, redis)
    return {sym: q.model_dump() for sym, q in quotes.items()}


# ── OHLCV history ──────────────────────────────────────────────────────────────
@router.get(
    "/stock/{symbol}/history",
    response_model=StockHistory,
    summary="Get OHLCV candlestick history",
)
async def get_history(
    symbol: str,
    period: str = Query(
        "1y",
        description="Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd, max",
    ),
    interval: str = Query(
        "1d",
        description="Bar interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo",
    ),
    redis=Depends(get_redis),
) -> StockHistory:
    """Return historical candlestick data for charting."""
    history = await mkt_service.fetch_history(
        _validate_symbol(symbol), period=period, interval=interval, redis=redis
    )
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History for '{symbol}' not found.",
        )
    return history


# ── Also expose history without /stock/ prefix ─────────────────────────────────
@router.get(
    "/history/{symbol}",
    response_model=StockHistory,
    summary="Alias: Get OHLCV history for a symbol",
)
async def get_history_alias(
    symbol: str,
    interval: str = Query("1D", description="Interval"),
    range: str = Query("3M", description="Range (3M, 6M, 1Y, 5Y)"),
    redis=Depends(get_redis),
) -> StockHistory:
    """Frontend-compatible alias mapping range/interval to yfinance params."""
    period_map = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "MAX": "max"}
    interval_map = {"1D": "1d", "1W": "1wk", "1M": "1mo", "1H": "1h", "15M": "15m", "5M": "5m"}
    period = period_map.get(range.upper(), "3mo")
    iv = interval_map.get(interval.upper(), "1d")
    history = await mkt_service.fetch_history(
        _validate_symbol(symbol), period=period, interval=iv, redis=redis
    )
    if history is None:
        raise HTTPException(status_code=404, detail=f"History for '{symbol}' not found.")
    return history


# ── News ───────────────────────────────────────────────────────────────────────
@router.get(
    "/stock/{symbol}/news",
    response_model=List[NewsItem],
    summary="Get latest news articles for a symbol",
)
async def get_news(
    symbol: str,
    redis=Depends(get_redis),
) -> List[NewsItem]:
    """Return the most recent news items for the given ticker."""
    return await mkt_service.fetch_news(_validate_symbol(symbol), redis)


@router.get(
    "/news/{symbol}",
    response_model=List[NewsItem],
    summary="Alias: Get latest news for a symbol",
)
async def get_news_alias(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    redis=Depends(get_redis),
) -> List[NewsItem]:
    """Frontend-compatible news alias."""
    news = await mkt_service.fetch_news(_validate_symbol(symbol), redis)
    return news[:limit]


# ── Search ─────────────────────────────────────────────────────────────────────
@router.get(
    "/search",
    response_model=List[StockSearch],
    summary="Search stocks by symbol or company name",
)
async def search(
    q: str = Query(..., min_length=1, max_length=100),
) -> List[StockSearch]:
    """Search for stocks matching the query string."""
    from app.market.yfinance_client import search_stocks
    return search_stocks(q)


# ── Market summary ─────────────────────────────────────────────────────────────
@router.get(
    "/summary",
    response_model=MarketSummary,
    summary="Get major market index snapshots",
)
async def market_summary(redis=Depends(get_redis)) -> MarketSummary:
    """Return S&P 500, NASDAQ, DOW, and VIX snapshots."""
    return await mkt_service.fetch_market_summary(redis)


# ── Trending / top movers ──────────────────────────────────────────────────────
@router.get(
    "/trending",
    response_model=List[StockQuote],
    summary="Get top-moving stocks by absolute % change",
)
async def trending(redis=Depends(get_redis)) -> List[StockQuote]:
    """Return the top 10 movers across the tracked universe."""
    return await mkt_service.fetch_trending(redis)


@router.get(
    "/gainers",
    response_model=List[StockQuote],
    summary="Get top gaining stocks",
)
async def top_gainers(
    limit: int = Query(10, ge=1, le=50),
    redis=Depends(get_redis),
) -> List[StockQuote]:
    """Return the top N stocks by positive % change today."""
    return await mkt_service.fetch_movers("gainers", limit, redis)


@router.get(
    "/losers",
    response_model=List[StockQuote],
    summary="Get top losing stocks",
)
async def top_losers(
    limit: int = Query(10, ge=1, le=50),
    redis=Depends(get_redis),
) -> List[StockQuote]:
    """Return the top N stocks by negative % change today."""
    return await mkt_service.fetch_movers("losers", limit, redis)


@router.get(
    "/active",
    response_model=List[StockQuote],
    summary="Get most actively traded stocks",
)
async def most_active(
    limit: int = Query(10, ge=1, le=50),
    redis=Depends(get_redis),
) -> List[StockQuote]:
    """Return the top N stocks by trading volume."""
    return await mkt_service.fetch_movers("active", limit, redis)


# ── Watchlist ──────────────────────────────────────────────────────────────────
@router.get(
    "/watchlist",
    response_model=List[WatchlistItemResponse],
    summary="Get the current user's watchlist with live prices",
)
async def get_watchlist(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> List[WatchlistItemResponse]:
    """Return all watchlisted symbols with their current quotes — fetched concurrently."""
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .order_by(WatchlistItem.added_at.desc())
    )
    items = result.scalars().all()

    if not items:
        return []

    # Fetch all quotes concurrently instead of N+1 sequential calls
    symbols = [item.symbol for item in items]
    quotes_dict = await mkt_service.fetch_multiple_quotes(symbols, redis)

    output: List[WatchlistItemResponse] = []
    for item in items:
        quote = quotes_dict.get(item.symbol)
        output.append(
            WatchlistItemResponse(
                symbol=item.symbol,
                added_at=item.added_at,
                quote=quote,
            )
        )
    return output


@router.post(
    "/watchlist/{symbol}",
    status_code=status.HTTP_201_CREATED,
    summary="Add a stock to the watchlist",
)
async def add_to_watchlist(
    symbol: str,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Add the given symbol to the authenticated user's watchlist."""
    symbol = _validate_symbol(symbol)

    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{symbol}' is already on your watchlist.",
        )

    item = WatchlistItem(
        id=uuid.uuid4(),
        user_id=current_user.id,
        symbol=symbol,
    )
    db.add(item)
    await db.flush()
    logger.info("User %s added %s to watchlist", current_user.username, symbol)
    return {"message": f"'{symbol}' added to watchlist."}


@router.post(
    "/watchlist",
    status_code=status.HTTP_201_CREATED,
    summary="Add a stock to the watchlist (body)",
)
async def add_to_watchlist_body(
    body: Dict[str, str],
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Add a symbol from JSON body {symbol: ...} to watchlist."""
    raw = body.get("symbol", "")
    if not raw:
        raise HTTPException(status_code=400, detail="'symbol' is required.")
    symbol = _validate_symbol(raw)

    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"'{symbol}' already in watchlist.")

    item = WatchlistItem(id=uuid.uuid4(), user_id=current_user.id, symbol=symbol)
    db.add(item)
    await db.flush()
    return {"message": f"'{symbol}' added to watchlist."}


@router.delete(
    "/watchlist/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a stock from the watchlist",
)
async def remove_from_watchlist(
    symbol: str,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove the given symbol from the authenticated user's watchlist."""
    symbol = _validate_symbol(symbol)
    result = await db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' not found in your watchlist.",
        )
    logger.info("User %s removed %s from watchlist", current_user.username, symbol)
    return None
