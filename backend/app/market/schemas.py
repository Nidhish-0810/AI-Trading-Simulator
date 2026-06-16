"""
Pydantic v2 schemas for market data endpoints.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OHLCVBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockQuote(BaseModel):
    symbol: str
    name: str = ""
    price: float
    previous_close: float = 0.0
    change: float
    change_pct: float
    volume: float
    avg_volume: float = 0.0
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    open: Optional[float] = None
    beta: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"
    exchange: str = ""
    timestamp: datetime


class StockHistory(BaseModel):
    symbol: str
    period: str
    interval: str
    bars: List[OHLCVBar]


class StockSearch(BaseModel):
    symbol: str
    name: str
    exchange: str = ""
    sector: str = ""
    market_cap: Optional[float] = None


class MarketIndex(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    timestamp: datetime


class MarketSummary(BaseModel):
    indices: List[MarketIndex]
    timestamp: datetime


class NewsItem(BaseModel):
    title: str
    url: str = ""
    source: str = ""
    published_at: Optional[str] = None
    summary: str = ""
    sentiment: Optional[float] = None


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    added_at: datetime
    quote: Optional[StockQuote] = None
