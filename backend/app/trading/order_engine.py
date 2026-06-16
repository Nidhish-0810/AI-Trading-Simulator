"""
Order matching engine: FIFO queue, partial fills, portfolio updates.
"""
import logging
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import settings
from app.core.exceptions import InsufficientFundsError, InsufficientSharesError, InvalidOrderError, NotFoundError
from app.core.redis_client import CacheKeys, get_cache, publish
from app.portfolio.models import Holding, Transaction
from app.trading.models import Order, Trade

logger = logging.getLogger(__name__)


class OrderEngine:
    def calculate_commission(self, quantity: Decimal, price: Decimal) -> Decimal:
        trade_value = quantity * price
        commission = trade_value * Decimal(str(settings.COMMISSION_RATE))
        return max(commission.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP), Decimal("0.01"))

    async def _get_current_price(self, redis, symbol: str) -> Decimal:
        from app.market.yfinance_client import get_quote as yf_get_quote
        cache_key = CacheKeys.stock_quote(symbol)
        cached = await get_cache(redis, cache_key)
        if cached and "price" in cached:
            return Decimal(str(cached["price"]))
        try:
            quote = await yf_get_quote(symbol)
            return Decimal(str(quote.price))
        except Exception as e:
            raise InvalidOrderError(f"Cannot fetch price for {symbol}: {e}")

    async def _check_sufficient_funds(self, user: User, quantity: Decimal, price: Decimal) -> None:
        total_cost = quantity * price + self.calculate_commission(quantity, price)
        if Decimal(str(user.balance)) < total_cost:
            raise InsufficientFundsError(required=float(total_cost), available=float(user.balance))

    async def _check_sufficient_shares(self, db: AsyncSession, user_id: uuid.UUID, symbol: str, quantity: Decimal) -> Holding:
        result = await db.execute(select(Holding).where(and_(Holding.user_id == user_id, Holding.symbol == symbol.upper())))
        holding = result.scalar_one_or_none()
        if not holding or holding.quantity < quantity:
            raise InsufficientSharesError(symbol=symbol, required=float(quantity), available=float(holding.quantity) if holding else 0.0)
        return holding

    async def _update_portfolio_buy(self, db: AsyncSession, user: User, symbol: str, quantity: Decimal, price: Decimal, commission: Decimal) -> None:
        total_cost = quantity * price + commission
        symbol = symbol.upper()
        result = await db.execute(select(Holding).where(and_(Holding.user_id == user.id, Holding.symbol == symbol)))
        holding = result.scalar_one_or_none()
        if holding:
            old_value = holding.quantity * holding.average_cost
            new_total_qty = holding.quantity + quantity
            holding.average_cost = (old_value + quantity * price) / new_total_qty
            holding.quantity = new_total_qty
        else:
            db.add(Holding(user_id=user.id, symbol=symbol, quantity=quantity, average_cost=price))
        user.balance = Decimal(str(user.balance)) - total_cost
        db.add(Transaction(user_id=user.id, transaction_type="buy", symbol=symbol, quantity=quantity, price=price, total_amount=quantity * price, balance_after=user.balance, notes=f"Buy {quantity} {symbol} @ ${price}"))

    async def _update_portfolio_sell(self, db: AsyncSession, user: User, symbol: str, quantity: Decimal, price: Decimal, commission: Decimal, holding: Holding) -> None:
        proceeds = quantity * price - commission
        holding.quantity -= quantity
        if holding.quantity <= Decimal("0.000001"):
            await db.delete(holding)
        user.balance = Decimal(str(user.balance)) + proceeds
        db.add(Transaction(user_id=user.id, transaction_type="sell", symbol=symbol.upper(), quantity=quantity, price=price, total_amount=quantity * price, balance_after=user.balance, notes=f"Sell {quantity} {symbol} @ ${price}"))

    async def _create_trade_record(self, db: AsyncSession, order: Order, quantity: Decimal, price: Decimal, commission: Decimal) -> Trade:
        trade = Trade(order_id=order.id, user_id=order.user_id, symbol=order.symbol, side=order.side, quantity=quantity, executed_price=price, total_value=quantity * price, commission=commission)
        db.add(trade)
        return trade

    async def _publish_trade_event(self, redis, user_id: uuid.UUID, trade: Trade, order: Order) -> None:
        await publish(redis, f"user:{user_id}", {"type": "trade_fill", "order_id": str(order.id), "symbol": trade.symbol, "side": trade.side, "quantity": float(trade.quantity), "price": float(trade.executed_price), "total_value": float(trade.total_value), "commission": float(trade.commission)})

    async def place_market_order(self, db: AsyncSession, redis, user: User, symbol: str, side: str, quantity: float) -> tuple[Order, Trade]:
        symbol = symbol.upper()
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise InvalidOrderError("Quantity must be positive")
        price = await self._get_current_price(redis, symbol)
        commission = self.calculate_commission(qty, price)
        holding = None
        if side == "buy":
            await self._check_sufficient_funds(user, qty, price)
        elif side == "sell":
            holding = await self._check_sufficient_shares(db, user.id, symbol, qty)
        else:
            raise InvalidOrderError(f"Invalid side: {side}")
        order = Order(user_id=user.id, symbol=symbol, order_type="market", side=side, quantity=qty, filled_quantity=qty, average_fill_price=price, status="filled")
        db.add(order)
        await db.flush()
        trade = await self._create_trade_record(db, order, qty, price, commission)
        if side == "buy":
            await self._update_portfolio_buy(db, user, symbol, qty, price, commission)
        else:
            await self._update_portfolio_sell(db, user, symbol, qty, price, commission, holding)
        await db.flush()
        await self._publish_trade_event(redis, user.id, trade, order)
        logger.info(f"Market order filled: {side.upper()} {qty} {symbol} @ ${price}")
        return order, trade

    async def place_limit_order(self, db: AsyncSession, redis, user: User, symbol: str, side: str, quantity: float, limit_price: float) -> Order:
        symbol, qty, lp = symbol.upper(), Decimal(str(quantity)), Decimal(str(limit_price))
        if qty <= 0 or lp <= 0:
            raise InvalidOrderError("Quantity and limit price must be positive")
        if side == "buy":
            await self._check_sufficient_funds(user, qty, lp)
        elif side == "sell":
            await self._check_sufficient_shares(db, user.id, symbol, qty)
        else:
            raise InvalidOrderError(f"Invalid side: {side}")
        order = Order(user_id=user.id, symbol=symbol, order_type="limit", side=side, quantity=qty, filled_quantity=Decimal("0"), limit_price=lp, status="pending")
        db.add(order)
        await db.flush()
        return order

    async def place_stop_loss_order(self, db: AsyncSession, redis, user: User, symbol: str, side: str, quantity: float, stop_price: float) -> Order:
        symbol, qty, sp = symbol.upper(), Decimal(str(quantity)), Decimal(str(stop_price))
        if qty <= 0 or sp <= 0:
            raise InvalidOrderError("Quantity and stop price must be positive")
        if side == "sell":
            await self._check_sufficient_shares(db, user.id, symbol, qty)
        elif side == "buy":
            await self._check_sufficient_funds(user, qty, sp)
        else:
            raise InvalidOrderError(f"Invalid side: {side}")
        order = Order(user_id=user.id, symbol=symbol, order_type="stop_loss", side=side, quantity=qty, filled_quantity=Decimal("0"), stop_price=sp, status="pending")
        db.add(order)
        await db.flush()
        return order

    async def cancel_order(self, db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        result = await db.execute(select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)))
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError("Order", str(order_id))
        if order.status in ("filled", "cancelled"):
            raise InvalidOrderError(f"Cannot cancel order with status '{order.status}'")
        order.status = "cancelled"
        await db.flush()
        return order


order_engine = OrderEngine()
