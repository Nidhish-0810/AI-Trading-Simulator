"""
Market service layer: wraps the yfinance client with Redis caching.

Cache TTLs:
  - Quotes      : 60 seconds
  - History     : 5 minutes
  - News        : 10 minutes
  - Summary     : 2 minutes
  - Trending    : 90 seconds
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.core.redis_client import get_cache, set_cache
from app.market import yfinance_client as yfc
from app.market.schemas import (
    MarketSummary,
    NewsItem,
    StockHistory,
    StockQuote,
    StockSearch,
)

logger = logging.getLogger(__name__)

# Cache TTLs (seconds)
QUOTE_TTL = 60
HISTORY_TTL = 300
NEWS_TTL = 600
SUMMARY_TTL = 120
TRENDING_TTL = 90


async def fetch_quote(
    symbol: str, redis=None
) -> Optional[StockQuote]:
    """Return a real-time (or recently cached) stock quote."""
    cache_key = f"quote:{symbol.upper()}"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return StockQuote(**cached)
            except Exception:
                pass

    quote = await yfc.get_quote(symbol.upper())
    if quote and redis is not None:
        await set_cache(redis, cache_key, quote.model_dump(), ttl=QUOTE_TTL)
    return quote


async def fetch_history(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    redis=None,
) -> Optional[StockHistory]:
    """Return OHLCV history, caching results for 5 minutes."""
    cache_key = f"history:{symbol.upper()}:{period}:{interval}"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return StockHistory(**cached)
            except Exception:
                pass

    history = await yfc.get_history(symbol.upper(), period=period, interval=interval)
    if history and redis is not None:
        await set_cache(redis, cache_key, history.model_dump(), ttl=HISTORY_TTL)
    return history


async def fetch_news(
    symbol: str, redis=None
) -> List[NewsItem]:
    """Return latest news, caching for 10 minutes."""
    cache_key = f"news:{symbol.upper()}"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return [NewsItem(**item) for item in cached]
            except Exception:
                pass

    news = await yfc.get_news(symbol.upper())
    if news and redis is not None:
        await set_cache(
            redis, cache_key, [n.model_dump() for n in news], ttl=NEWS_TTL
        )
    return news


async def fetch_market_summary(redis=None) -> MarketSummary:
    """Return major market indices, caching for 2 minutes."""
    cache_key = "market:summary"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return MarketSummary(**cached)
            except Exception:
                pass

    summary = await yfc.get_market_summary()
    if redis is not None:
        await set_cache(redis, cache_key, summary.model_dump(), ttl=SUMMARY_TTL)
    return summary


async def fetch_trending(redis=None) -> List[StockQuote]:
    """Return top movers, caching for 90 seconds."""
    cache_key = "market:trending"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return [StockQuote(**q) for q in cached]
            except Exception:
                pass

    quotes = await yfc.get_trending_stocks()
    if redis is not None:
        await set_cache(
            redis, cache_key, [q.model_dump() for q in quotes], ttl=TRENDING_TTL
        )
    return quotes


async def fetch_movers(
    mover_type: str = "gainers",  # "gainers" | "losers" | "active"
    limit: int = 10,
    redis=None,
) -> List[StockQuote]:
    """
    Return top gainers, losers, or most-active stocks.
    Uses a sample of 40 popular stocks and sorts by change_pct or volume.
    Cached for 90 seconds.
    """
    cache_key = f"market:movers:{mover_type}:{limit}"

    if redis is not None:
        cached = await get_cache(redis, cache_key)
        if cached:
            try:
                return [StockQuote(**q) for q in cached]
            except Exception:
                pass

    # Sample 40 popular stocks for mover detection
    sample_symbols = [s["symbol"] for s in yfc.POPULAR_STOCKS[:40]]
    quotes_dict = await fetch_multiple_quotes(sample_symbols, redis)
    quotes = list(quotes_dict.values())

    if mover_type == "gainers":
        sorted_quotes = sorted(quotes, key=lambda q: q.change_pct, reverse=True)
    elif mover_type == "losers":
        sorted_quotes = sorted(quotes, key=lambda q: q.change_pct)
    else:  # active
        sorted_quotes = sorted(quotes, key=lambda q: q.volume or 0, reverse=True)

    result = sorted_quotes[:limit]
    if redis is not None:
        await set_cache(redis, cache_key, [q.model_dump() for q in result], ttl=TRENDING_TTL)
    return result


async def fetch_multiple_quotes(
    symbols: List[str], redis=None
) -> Dict[str, StockQuote]:
    """Fetch quotes for a list of symbols concurrently using individual caches."""
    tasks = [fetch_quote(sym, redis) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output: Dict[str, StockQuote] = {}
    for sym, result in zip(symbols, results):
        if isinstance(result, StockQuote):
            output[sym] = result
    return output


def get_all_stocks(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    sector: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return a paginated slice of the stock catalogue, optionally filtered.
    """
    stocks = yfc.POPULAR_STOCKS

    if search:
        q = search.lower()
        stocks = [
            s
            for s in stocks
            if q in s["symbol"].lower() or q in s["name"].lower()
        ]

    if sector:
        stocks = [s for s in stocks if s.get("sector", "").lower() == sector.lower()]

    total = len(stocks)
    start = (page - 1) * page_size
    end = start + page_size
    page_stocks = stocks[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "stocks": [
            StockSearch(
                symbol=s["symbol"],
                name=s["name"],
                sector=s.get("sector", ""),
            )
            for s in page_stocks
        ],
    }
