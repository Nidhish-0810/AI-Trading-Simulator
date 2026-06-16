"""
Pydantic v2 schemas for portfolio endpoints.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    symbol: str
    quantity: float
    average_cost: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    total_cost: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None


class PortfolioSummary(BaseModel):
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
    holdings: List[HoldingResponse]
    summary: PortfolioSummary


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    transaction_type: str
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    total_amount: float
    created_at: datetime


class PortfolioHistoryPoint(BaseModel):
    date: str
    value: float
    cash: float
    invested: float


class PortfolioAnalytics(BaseModel):
    sharpe_ratio: Optional[float] = Field(None)
    beta: Optional[float] = Field(None)
    alpha: Optional[float] = Field(None)
    max_drawdown: Optional[float] = Field(None)
    volatility: Optional[float] = Field(None)
    win_rate: Optional[float] = Field(None)
    total_return: Optional[float] = Field(None)
    sector_allocation: Dict[str, float] = Field(default_factory=dict)
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = Field(default_factory=list)
