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
from app.core.exceptions import (
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidOrderError,
    NotFoundError,
)
from app.core.redis_client import Redis, CacheKeys, get_cache, publish
from app.portfolio.models import Holding, Transaction
from app.trading.models import Order, Trade

logger = logging.getLogger(__name__)


class OrderEngine:
    """
    Core order matching engine for TradeAI.

    Handles:
    - Market orders (instant fill at current price)
    - Limit orders (queued, filled when price is reached)
    - Stop-loss orders (triggered when price drops to stop level)
    - Portfolio updates (holdings + balance)
    - Commission calculation (0.1% of trade value)
    """

    def calculate_commission(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Calculate trading commission: 0.1% of trade value, min $0.01."""
        trade_value = quantity * price
        commission = trade_value * Decimal(str(settings.COMMISSION_RATE))
        return max(commission.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP), Decimal("0.01"))

    async def _get_current_price(self, redis: Redis, symbol: str) -> Decimal:
        """Fetch current price from Redis cache, or from yfinance if not cached."""
        from app.market.yfinance_client import get_quote as yf_get_quote

        # Try Redis cache first
        cache_key = CacheKeys.stock_quote(symbol)
        cached = await get_cache(redis, cache_key)
        if cached and "price" in cached:
            return Decimal(str(cached["price"]))

        # Fall back to yfinance
        try:
            quote = await yf_get_quote(symbol)
            return Decimal(str(quote["price"]))
        except Exception as e:
            raise InvalidOrderError(f"Cannot fetch price for {symbol}: {e}")

    async def _check_sufficient_funds(
        self, user: User, quantity: Decimal, price: Decimal
    ) -> None:
        """Verify user has enough balance for a buy order + commission."""
        trade_value = quantity * price
        commission = self.calculate_commission(quantity, price)
        total_cost = trade_value + commission

        if Decimal(str(user.balance)) < total_cost:
            raise InsufficientFundsError(
                required=float(total_cost),
                available=float(user.balance),
            )

    async def _check_sufficient_shares(
        self, db: AsyncSession, user_id: uuid.UUID, symbol: str, quantity: Decimal
    ) -> Holding:
        """Verify user holds enough shares for a sell order."""
        result = await db.execute(
            select(Holding).where(
                and_(Holding.user_id == user_id, Holding.symbol == symbol.upper())
            )
        )
        holding = result.scalar_one_or_none()

        if not holding or holding.quantity < quantity:
            available = float(holding.quantity) if holding else 0.0
            raise InsufficientSharesError(
                symbol=symbol,
                required=float(quantity),
                available=available,
            )
        return holding

    async def _update_portfolio_buy(
        self,
        db: AsyncSession,
        user: User,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
    ) -> None:
        """Update holdings and balance after a BUY fill."""
        total_cost = quantity * price + commission
        symbol = symbol.upper()

        # Update or create holding
        result = await db.execute(
            select(Holding).where(
                and_(Holding.user_id == user.id, Holding.symbol == symbol)
            )
        )
        holding = result.scalar_one_or_none()

        if holding:
            # Recalculate average cost
            old_value = holding.quantity * holding.average_cost
            new_value = quantity * price
            new_total_qty = holding.quantity + quantity
            holding.average_cost = (old_value + new_value) / new_total_qty
            holding.quantity = new_total_qty
        else:
            holding = Holding(
                user_id=user.id,
                symbol=symbol,
                quantity=quantity,
                average_cost=price,
            )
            db.add(holding)

        # Deduct from balance
        user.balance = Decimal(str(user.balance)) - total_cost

        # Record transaction
        tx = Transaction(
            user_id=user.id,
            transaction_type="buy",
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_amount=quantity * price,
            balance_after=user.balance,
            notes=f"Market buy {quantity} {symbol} @ ${price}",
        )
        db.add(tx)

        # Record commission transaction
        if commission > 0:
            comm_tx = Transaction(
                user_id=user.id,
                transaction_type="commission",
                symbol=symbol,
                quantity=None,
                price=None,
                total_amount=commission,
                balance_after=user.balance,
                notes=f"Commission for {symbol} trade",
            )
            db.add(comm_tx)

    async def _update_portfolio_sell(
        self,
        db: AsyncSession,
        user: User,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
        holding: Holding,
    ) -> None:
        """Update holdings and balance after a SELL fill."""
        symbol = symbol.upper()
        proceeds = quantity * price - commission

        # Update holding
        holding.quantity -= quantity
        if holding.quantity <= Decimal("0.000001"):
            await db.delete(holding)

        # Credit to balance
        user.balance = Decimal(str(user.balance)) + proceeds

        # Record transaction
        tx = Transaction(
            user_id=user.id,
            transaction_type="sell",
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_amount=quantity * price,
            balance_after=user.balance,
            notes=f"Market sell {quantity} {symbol} @ ${price}",
        )
        db.add(tx)

        # Commission transaction
        if commission > 0:
            comm_tx = Transaction(
                user_id=user.id,
                transaction_type="commission",
                symbol=symbol,
                total_amount=commission,
                balance_after=user.balance,
                notes=f"Commission for {symbol} trade",
            )
            db.add(comm_tx)

    async def _create_trade_record(
        self,
        db: AsyncSession,
        order: Order,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
    ) -> Trade:
        """Create an immutable Trade record for a fill."""
        trade = Trade(
            order_id=order.id,
            user_id=order.user_id,
            symbol=order.symbol,
            side=order.side,
            quantity=quantity,
            executed_price=price,
            total_value=quantity * price,
            commission=commission,
        )
        db.add(trade)
        return trade

    async def _publish_trade_event(
        self, redis: Redis, user_id: uuid.UUID, trade: Trade, order: Order
    ) -> None:
        """Publish trade fill event for WebSocket broadcast."""
        await publish(redis, f"user:{user_id}", {
            "type": "trade_fill",
            "order_id": str(order.id),
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": float(trade.quantity),
            "price": float(trade.executed_price),
            "total_value": float(trade.total_value),
            "commission": float(trade.commission),
            "order_status": order.status,
        })

    # ─── Public API ───────────────────────────────────────────────────────────
    async def place_market_order(
        self,
        db: AsyncSession,
        redis: Redis,
        user: User,
        symbol: str,
        side: str,
        quantity: float,
    ) -> tuple[Order, Trade]:
        """
        Execute a market order immediately at current price.

        Args:
            db: Database session
            redis: Redis client
            user: Authenticated user
            symbol: Stock ticker symbol
            side: 'buy' or 'sell'
            quantity: Number of shares

        Returns:
            (Order, Trade) tuple

        Raises:
            InsufficientFundsError, InsufficientSharesError, InvalidOrderError
        """
        symbol = symbol.upper()
        qty = Decimal(str(quantity))

        if qty <= 0:
            raise InvalidOrderError("Quantity must be positive")

        # Fetch current market price
        price = await self._get_current_price(redis, symbol)

        # Validate
        commission = self.calculate_commission(qty, price)
        holding = None

        if side == "buy":
            await self._check_sufficient_funds(user, qty, price)
        elif side == "sell":
            holding = await self._check_sufficient_shares(db, user.id, symbol, qty)
        else:
            raise InvalidOrderError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        # Create Order record
        order = Order(
            user_id=user.id,
            symbol=symbol,
            order_type="market",
            side=side,
            quantity=qty,
            filled_quantity=qty,
            average_fill_price=price,
            status="filled",
        )
        db.add(order)
        await db.flush()

        # Create Trade record
        trade = await self._create_trade_record(db, order, qty, price, commission)

        # Update portfolio
        if side == "buy":
            await self._update_portfolio_buy(db, user, symbol, qty, price, commission)
        else:
            await self._update_portfolio_sell(db, user, symbol, qty, price, commission, holding)

        await db.flush()

        # Publish event
        await self._publish_trade_event(redis, user.id, trade, order)

        logger.info(
            f"Market order filled: {side.upper()} {qty} {symbol} "
            f"@ ${price} commission=${commission} user={user.username}"
        )
        return order, trade

    async def place_limit_order(
        self,
        db: AsyncSession,
        redis: Redis,
        user: User,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
    ) -> Order:
        """
        Queue a limit order. Will be filled when market price reaches limit_price.

        For BUY limits: fills when market price drops to or below limit_price.
        For SELL limits: fills when market price rises to or above limit_price.
        """
        symbol = symbol.upper()
        qty = Decimal(str(quantity))
        lp = Decimal(str(limit_price))

        if qty <= 0:
            raise InvalidOrderError("Quantity must be positive")
        if lp <= 0:
            raise InvalidOrderError("Limit price must be positive")

        # For buy limit: pre-check funds at limit price
        if side == "buy":
            await self._check_sufficient_funds(user, qty, lp)
        elif side == "sell":
            await self._check_sufficient_shares(db, user.id, symbol, qty)
        else:
            raise InvalidOrderError(f"Invalid side: {side}")

        order = Order(
            user_id=user.id,
            symbol=symbol,
            order_type="limit",
            side=side,
            quantity=qty,
            filled_quantity=Decimal("0"),
            limit_price=lp,
            status="pending",
        )
        db.add(order)
        await db.flush()

        logger.info(
            f"Limit order queued: {side.upper()} {qty} {symbol} @ ${lp} user={user.username}"
        )
        return order

    async def place_stop_loss_order(
        self,
        db: AsyncSession,
        redis: Redis,
        user: User,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
    ) -> Order:
        """
        Queue a stop-loss order. Converts to market order when stop_price is reached.

        Typically used for SELL orders to cap downside loss.
        """
        symbol = symbol.upper()
        qty = Decimal(str(quantity))
        sp = Decimal(str(stop_price))

        if qty <= 0:
            raise InvalidOrderError("Quantity must be positive")
        if sp <= 0:
            raise InvalidOrderError("Stop price must be positive")

        if side == "sell":
            await self._check_sufficient_shares(db, user.id, symbol, qty)
        elif side == "buy":
            await self._check_sufficient_funds(user, qty, sp)
        else:
            raise InvalidOrderError(f"Invalid side: {side}")

        order = Order(
            user_id=user.id,
            symbol=symbol,
            order_type="stop_loss",
            side=side,
            quantity=qty,
            filled_quantity=Decimal("0"),
            stop_price=sp,
            status="pending",
        )
        db.add(order)
        await db.flush()

        logger.info(
            f"Stop-loss order queued: {side.upper()} {qty} {symbol} @ stop=${sp} user={user.username}"
        )
        return order

    async def match_limit_orders(
        self,
        db: AsyncSession,
        redis: Redis,
        symbol: str,
        current_price: Decimal,
    ) -> list[Order]:
        """
        FIFO matching: scan pending orders for symbol and fill those whose
        limit/stop conditions are now met. Called periodically by the price feed.
        """
        symbol = symbol.upper()
        filled_orders = []

        # Fetch pending orders for this symbol (FIFO by created_at)
        result = await db.execute(
            select(Order)
            .where(
                and_(
                    Order.symbol == symbol,
                    Order.status.in_(["pending", "partial"]),
                    Order.order_type.in_(["limit", "stop_loss"]),
                )
            )
            .order_by(Order.created_at)
        )
        orders = list(result.scalars().all())

        for order in orders:
            should_fill = False

            if order.order_type == "limit":
                # BUY limit: fill when price drops to or below limit
                if order.side == "buy" and current_price <= order.limit_price:
                    should_fill = True
                # SELL limit: fill when price rises to or above limit
                elif order.side == "sell" and current_price >= order.limit_price:
                    should_fill = True
            elif order.order_type == "stop_loss":
                # Stop triggers when price falls to or below stop (for sell)
                if order.side == "sell" and current_price <= order.stop_price:
                    should_fill = True
                elif order.side == "buy" and current_price >= order.stop_price:
                    should_fill = True

            if not should_fill:
                continue

            # Get user for balance update
            from app.auth.service import get_user_by_id
            user = await get_user_by_id(db, order.user_id)
            if not user:
                continue

            try:
                remaining_qty = order.quantity - order.filled_quantity
                commission = self.calculate_commission(remaining_qty, current_price)
                holding = None

                if order.side == "buy":
                    await self._check_sufficient_funds(user, remaining_qty, current_price)
                    await self._update_portfolio_buy(
                        db, user, symbol, remaining_qty, current_price, commission
                    )
                else:
                    holding = await self._check_sufficient_shares(
                        db, order.user_id, symbol, remaining_qty
                    )
                    await self._update_portfolio_sell(
                        db, user, symbol, remaining_qty, current_price, commission, holding
                    )

                # Update order
                order.filled_quantity = order.quantity
                order.average_fill_price = current_price
                order.status = "filled"

                # Create trade record
                trade = await self._create_trade_record(
                    db, order, remaining_qty, current_price, commission
                )

                await self._publish_trade_event(redis, user.id, trade, order)
                filled_orders.append(order)

                logger.info(
                    f"Limit/Stop order matched: {order.side.upper()} {remaining_qty} "
                    f"{symbol} @ ${current_price} order_id={order.id}"
                )

            except (InsufficientFundsError, InsufficientSharesError) as e:
                # Cancel order if can't fill
                order.status = "cancelled"
                order.notes = f"Auto-cancelled: {e}"
                logger.warning(f"Order {order.id} auto-cancelled: {e}")

        await db.flush()
        return filled_orders

    async def cancel_order(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> Order:
        """Cancel a pending limit or stop-loss order."""
        result = await db.execute(
            select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
        )
        order = result.scalar_one_or_none()

        if not order:
            raise NotFoundError("Order", str(order_id))

        if order.status in ("filled", "cancelled"):
            raise InvalidOrderError(
                f"Cannot cancel order with status '{order.status}'"
            )

        if order.order_type == "market":
            raise InvalidOrderError("Cannot cancel a market order (already filled)")

        order.status = "cancelled"
        await db.flush()

        logger.info(f"Order cancelled: {order_id} by user={user_id}")
        return order


# ─── Singleton instance ───────────────────────────────────────────────────────
order_engine = OrderEngine()
