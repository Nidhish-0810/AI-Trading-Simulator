"""
Pydantic v2 schemas for portfolio endpoints.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HoldingResponse(BaseModel):
    """A single holding with enriched live market data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    quantity: float
    average_cost: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    total_cost: Optional[float] = None
    pnl: Optional[float] = None  # unrealised P&L in dollars
    pnl_pct: Optional[float] = None  # unrealised P&L %
    day_change: Optional[float] = None  # daily $ change
    day_change_pct: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Quick-view portfolio summary card."""

    cash_balance: float
    portfolio_value: float
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float
    day_pnl_pct: float
    num_positions: int


class PortfolioResponse(BaseModel):
    """Full portfolio response with holdings and summary."""

    holdings: List[HoldingResponse]
    summary: PortfolioSummary


class TransactionResponse(BaseModel):
    """Single transaction ledger entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    total_amount: float
    created_at: datetime


class PortfolioHistoryPoint(BaseModel):
    """Portfolio value at a specific date."""

    date: str
    value: float
    cash: float
    invested: float


class PortfolioAnalytics(BaseModel):
    """Comprehensive portfolio analytics."""

    sharpe_ratio: Optional[float] = Field(None, description="Annualised Sharpe ratio")
    beta: Optional[float] = Field(None, description="Beta vs S&P 500")
    alpha: Optional[float] = Field(None, description="Jensen's Alpha (annualised)")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown %")
    volatility: Optional[float] = Field(None, description="Annualised std dev of returns")
    win_rate: Optional[float] = Field(None, description="% of profitable sell trades")
    total_return: Optional[float] = Field(None, description="Total return % since inception")
    sector_allocation: Dict[str, float] = Field(
        default_factory=dict, description="Sector → % of portfolio value"
    )
    top_performers: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top 5 holdings by P&L %"
    )
    worst_performers: List[Dict[str, Any]] = Field(
        default_factory=list, description="Bottom 5 holdings by P&L %"
    )
