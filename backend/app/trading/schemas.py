"""
Pydantic v2 schemas for trading endpoints.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateOrder(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    order_type: str = Field(..., description="market | limit | stop_loss")
    side: str = Field(..., description="buy | sell")
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)

    @field_validator("order_type")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        if v.lower() not in {"market", "limit", "stop_loss"}:
            raise ValueError("order_type must be market, limit, or stop_loss")
        return v.lower()

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v.lower() not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class TradeResponse(BaseModel):
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
    trades: List[TradeResponse] = []


class OrderBookEntry(BaseModel):
    price: float
    quantity: float
    order_count: int


class OrderBook(BaseModel):
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    spread: float
    mid_price: float
