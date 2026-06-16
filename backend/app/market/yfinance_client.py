"""
yfinance wrapper providing async-compatible (thread-pool) calls for all
market data needs: quotes, OHLCV history, search, indices, and news.
"""
import asyncio
import logging
from datetime import datetime, timezone
from functools import partial
from typing import Any, Dict, List, Optional

import yfinance as yf

from app.market.schemas import MarketIndex, MarketSummary, NewsItem, OHLCVBar, StockHistory, StockQuote, StockSearch

logger = logging.getLogger(__name__)

POPULAR_STOCKS: List[Dict[str, str]] = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "QCOM", "name": "Qualcomm Inc.", "sector": "Technology"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology"},
    {"symbol": "IBM", "name": "IBM Corporation", "sector": "Technology"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
    {"symbol": "NOW", "name": "ServiceNow Inc.", "sector": "Technology"},
    {"symbol": "SNOW", "name": "Snowflake Inc.", "sector": "Technology"},
    {"symbol": "PLTR", "name": "Palantir Technologies", "sector": "Technology"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Financial Services"},
    {"symbol": "GS", "name": "Goldman Sachs Group", "sector": "Financial Services"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Financial Services"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financial Services"},
    {"symbol": "WFC", "name": "Wells Fargo & Co.", "sector": "Financial Services"},
    {"symbol": "PYPL", "name": "PayPal Holdings Inc.", "sector": "Financial Services"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway B", "sector": "Financial Services"},
    {"symbol": "AXP", "name": "American Express Co.", "sector": "Financial Services"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "AMGN", "name": "Amgen Inc.", "sector": "Healthcare"},
    {"symbol": "GILD", "name": "Gilead Sciences Inc.", "sector": "Healthcare"},
    {"symbol": "LLY", "name": "Eli Lilly and Co.", "sector": "Healthcare"},
    {"symbol": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive"},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Defensive"},
    {"symbol": "KO", "name": "The Coca-Cola Company", "sector": "Consumer Defensive"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Defensive"},
    {"symbol": "MCD", "name": "McDonald's Corporation", "sector": "Consumer Cyclical"},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Consumer Cyclical"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "HD", "name": "The Home Depot Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "DIS", "name": "The Walt Disney Company", "sector": "Communication Services"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy"},
    {"symbol": "T", "name": "AT&T Inc.", "sector": "Communication Services"},
    {"symbol": "VZ", "name": "Verizon Communications", "sector": "Communication Services"},
    {"symbol": "BA", "name": "The Boeing Company", "sector": "Industrials"},
    {"symbol": "HON", "name": "Honeywell International", "sector": "Industrials"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "sector": "ETF"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "sector": "ETF"},
    {"symbol": "COIN", "name": "Coinbase Global Inc.", "sector": "Financial Services"},
    {"symbol": "MSTR", "name": "MicroStrategy Inc.", "sector": "Technology"},
    {"symbol": "SHOP", "name": "Shopify Inc.", "sector": "Technology"},
    {"symbol": "UBER", "name": "Uber Technologies Inc.", "sector": "Technology"},
    {"symbol": "ABNB", "name": "Airbnb Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "SOFI", "name": "SoFi Technologies Inc.", "sector": "Financial Services"},
]

STOCK_LOOKUP: Dict[str, Dict[str, str]] = {s["symbol"]: s for s in POPULAR_STOCKS}
INDEX_SYMBOLS: Dict[str, str] = {
    "^GSPC": "S&P 500", "^IXIC": "NASDAQ Composite",
    "^DJI": "Dow Jones Industrial", "^VIX": "CBOE Volatility Index",
}


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        result = float(value)
        return default if result != result else result
    except (TypeError, ValueError):
        return default


def _fetch_quote_sync(symbol: str) -> Optional[StockQuote]:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        slow_info = ticker.info
        price = _safe_float(getattr(info, "last_price", None)) or _safe_float(slow_info.get("currentPrice"))
        if price is None:
            return None
        prev_close = _safe_float(getattr(info, "previous_close", None)) or _safe_float(slow_info.get("previousClose"), price)
        change = (price - prev_close) if prev_close else 0.0
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        meta = STOCK_LOOKUP.get(symbol, {})
        return StockQuote(
            symbol=symbol,
            name=slow_info.get("longName") or slow_info.get("shortName") or meta.get("name", symbol),
            price=round(price, 4), previous_close=round(prev_close or 0.0, 4),
            change=round(change, 4), change_pct=round(change_pct, 4),
            volume=_safe_float(slow_info.get("volume"), 0.0),
            avg_volume=_safe_float(slow_info.get("averageVolume"), 0.0),
            market_cap=_safe_float(slow_info.get("marketCap")),
            pe_ratio=_safe_float(slow_info.get("trailingPE")),
            eps=_safe_float(slow_info.get("trailingEps")),
            dividend_yield=_safe_float(slow_info.get("dividendYield")),
            week_52_high=_safe_float(slow_info.get("fiftyTwoWeekHigh")),
            week_52_low=_safe_float(slow_info.get("fiftyTwoWeekLow")),
            day_high=_safe_float(slow_info.get("dayHigh")),
            day_low=_safe_float(slow_info.get("dayLow")),
            open=_safe_float(slow_info.get("open")),
            beta=_safe_float(slow_info.get("beta")),
            sector=slow_info.get("sector") or meta.get("sector"),
            industry=slow_info.get("industry"),
            currency=slow_info.get("currency", "USD"),
            exchange=slow_info.get("exchange", ""),
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.warning("Failed to fetch quote for %s: %s", symbol, exc)
        return None


def _fetch_history_sync(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[StockHistory]:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        bars = [OHLCVBar(
            date=str(idx.date()) if hasattr(idx, "date") else str(idx),
            open=round(float(row.get("Open", 0)), 4), high=round(float(row.get("High", 0)), 4),
            low=round(float(row.get("Low", 0)), 4), close=round(float(row.get("Close", 0)), 4),
            volume=round(float(row.get("Volume", 0)), 0),
        ) for idx, row in df.iterrows()]
        return StockHistory(symbol=symbol, period=period, interval=interval, bars=bars)
    except Exception as exc:
        logger.warning("Failed to fetch history for %s: %s", symbol, exc)
        return None


def _fetch_news_sync(symbol: str) -> List[NewsItem]:
    try:
        raw_news = yf.Ticker(symbol).news or []
        return [NewsItem(
            title=a.get("title", ""), url=a.get("link", ""), source=a.get("publisher", ""),
            published_at=str(datetime.fromtimestamp(a.get("providerPublishTime", 0), tz=timezone.utc)),
            summary=a.get("summary", ""),
        ) for a in raw_news[:10]]
    except Exception as exc:
        logger.warning("Failed to fetch news for %s: %s", symbol, exc)
        return []


async def get_quote(symbol: str) -> Optional[StockQuote]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_quote_sync, symbol)


async def get_history(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[StockHistory]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_fetch_history_sync, symbol, period, interval))


async def get_multiple_quotes(symbols: List[str]) -> Dict[str, StockQuote]:
    tasks = [get_quote(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {sym: r for sym, r in zip(symbols, results) if isinstance(r, StockQuote)}


def search_stocks(query: str) -> List[StockSearch]:
    q = query.lower().strip()
    if not q:
        return [StockSearch(symbol=s["symbol"], name=s["name"], sector=s.get("sector", "")) for s in POPULAR_STOCKS[:20]]
    return [StockSearch(symbol=s["symbol"], name=s["name"], sector=s.get("sector", ""))
            for s in POPULAR_STOCKS if q in s["symbol"].lower() or q in s["name"].lower()][:20]


def _fetch_index_sync(symbol: str, name: str) -> Optional[MarketIndex]:
    try:
        info = yf.Ticker(symbol).fast_info
        price = _safe_float(getattr(info, "last_price", None))
        prev_close = _safe_float(getattr(info, "previous_close", None))
        if price is None:
            return None
        change = price - (prev_close or price)
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        return MarketIndex(symbol=symbol, name=name, price=round(price, 2),
                          change=round(change, 2), change_pct=round(change_pct, 2),
                          timestamp=datetime.now(timezone.utc))
    except Exception as exc:
        logger.warning("Failed to fetch index %s: %s", symbol, exc)
        return None


async def get_market_summary() -> MarketSummary:
    loop = asyncio.get_running_loop()
    tasks = [loop.run_in_executor(None, partial(_fetch_index_sync, sym, name)) for sym, name in INDEX_SYMBOLS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    indices = [r for r in results if isinstance(r, MarketIndex)]
    return MarketSummary(indices=indices, timestamp=datetime.now(timezone.utc))


async def get_news(symbol: str) -> List[NewsItem]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_fetch_news_sync, symbol))


async def get_trending_stocks(limit: int = 10) -> List[StockQuote]:
    sample_symbols = [s["symbol"] for s in POPULAR_STOCKS[:30]]
    quotes = await get_multiple_quotes(sample_symbols)
    return sorted(quotes.values(), key=lambda q: abs(q.change_pct), reverse=True)[:limit]
