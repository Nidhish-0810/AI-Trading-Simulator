"""
Trading service: wrapper around OrderEngine.
"""
import logging
import uuid
from typing import List, Optional
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.trading.models import Order, Trade
from app.trading.order_engine import order_engine
from app.trading.schemas import CreateOrder, OrderBook, OrderBookEntry

logger = logging.getLogger(__name__)


async def place_order(db: AsyncSession, redis, user, schema: CreateOrder) -> Order:
    if schema.order_type == "market":
        order, _ = await order_engine.place_market_order(db, redis, user, schema.symbol, schema.side, schema.quantity)
        return order
    elif schema.order_type == "limit":
        if schema.price is None:
            from app.core.exceptions import InvalidOrderError
            raise InvalidOrderError("Limit orders require a 'price' field.")
        return await order_engine.place_limit_order(db, redis, user, schema.symbol, schema.side, schema.quantity, schema.price)
    elif schema.order_type == "stop_loss":
        if schema.stop_price is None:
            from app.core.exceptions import InvalidOrderError
            raise InvalidOrderError("Stop-loss orders require a 'stop_price' field.")
        return await order_engine.place_stop_loss_order(db, redis, user, schema.symbol, schema.side, schema.quantity, schema.stop_price)
    else:
        from app.core.exceptions import InvalidOrderError
        raise InvalidOrderError(f"Unknown order type: {schema.order_type}")


async def get_user_orders(db: AsyncSession, user_id: uuid.UUID, status_filter: Optional[str] = None, symbol_filter: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Order]:
    stmt = select(Order).where(Order.user_id == user_id)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter.lower())
    if symbol_filter:
        stmt = stmt.where(Order.symbol == symbol_filter.upper())
    stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_order_by_id(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    return result.scalar_one_or_none()


async def cancel_user_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    return await order_engine.cancel_order(db, user_id, order_id)


async def get_user_trades(db: AsyncSession, user_id: uuid.UUID, symbol_filter: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Trade]:
    stmt = select(Trade).where(Trade.user_id == user_id)
    if symbol_filter:
        stmt = stmt.where(Trade.symbol == symbol_filter.upper())
    stmt = stmt.order_by(Trade.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_virtual_order_book(db: AsyncSession, symbol: str, depth: int = 10) -> OrderBook:
    result = await db.execute(
        select(Order).where(Order.symbol == symbol.upper(), Order.status == "pending", Order.order_type == "limit")
    )
    pending_orders = result.scalars().all()
    buy_levels: dict = defaultdict(lambda: {"qty": 0.0, "count": 0})
    sell_levels: dict = defaultdict(lambda: {"qty": 0.0, "count": 0})
    for order in pending_orders:
        price = round(float(order.limit_price or 0), 2)
        remaining = float(order.quantity) - float(order.filled_quantity)
        level = buy_levels[price] if order.side == "buy" else sell_levels[price]
        level["qty"] += remaining
        level["count"] += 1
    bids = sorted([OrderBookEntry(price=p, quantity=v["qty"], order_count=v["count"]) for p, v in buy_levels.items()], key=lambda x: x.price, reverse=True)[:depth]
    asks = sorted([OrderBookEntry(price=p, quantity=v["qty"], order_count=v["count"]) for p, v in sell_levels.items()], key=lambda x: x.price)[:depth]
    best_bid = bids[0].price if bids else 0.0
    best_ask = asks[0].price if asks else 0.0
    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0.0
    return OrderBook(symbol=symbol.upper(), bids=bids, asks=asks, spread=round(spread, 4), mid_price=round(mid_price, 4))
