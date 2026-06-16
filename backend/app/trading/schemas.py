"""
Pydantic v2 schemas for trading endpoints.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────
class CreateOrder(BaseModel):
    """Request body for placing a new order."""

    symbol: str = Field(..., min_length=1, max_length=20)
    order_type: str = Field(..., description="market | limit | stop_loss")
    side: str = Field(..., description="buy | sell")
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: Optional[float] = Field(
        None, gt=0, description="Limit price (required for limit orders)"
    )
    stop_price: Optional[float] = Field(
        None, gt=0, description="Stop price (required for stop-loss orders)"
    )

    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        allowed = {"market", "limit", "stop_loss"}
        if v.lower() not in allowed:
            raise ValueError(f"order_type must be one of {allowed}")
        return v.lower()

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v.lower() not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


# ── Response schemas ───────────────────────────────────────────────────────────
class TradeResponse(BaseModel):
    """Single executed trade."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    side: str
    quantity: float
    executed_price: float
    total_value: float
    commission: float
    created_at: datetime


class OrderResponse(BaseModel):
    """Full order record including nested trades."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    order_type: str
    side: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: float
    status: str
    created_at: datetime
    updated_at: datetime


class OrderBookEntry(BaseModel):
    """A single price level in a virtual order book."""

    price: float
    quantity: float
    order_count: int


class OrderBook(BaseModel):
    """Virtual order book for a symbol with bids and asks."""

    symbol: str
    bids: List[OrderBookEntry]  # buy side, sorted highest first
    asks: List[OrderBookEntry]  # sell side, sorted lowest first
    spread: float
    mid_price: float
