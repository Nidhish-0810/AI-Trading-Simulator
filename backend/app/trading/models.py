"""
Trading models: Order, Trade, WatchlistItem.
"""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class Order(Base):
    """
    Represents a trading order (market, limit, or stop-loss).
    Status progresses: pending → partial → filled | cancelled
    """

    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Order classification
    order_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # market | limit | stop_loss
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy | sell

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False
    )
    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False, default=Decimal("0")
    )

    # Prices
    limit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2), nullable=True
    )  # For limit orders
    stop_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2), nullable=True
    )  # For stop-loss orders
    average_fill_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2), nullable=True
    )  # Computed after fills

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | partial | filled | cancelled | rejected

    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Order {self.side.upper()} {self.quantity} {self.symbol} "
            f"@ {self.order_type} status={self.status}>"
        )


class Trade(Base):
    """
    Immutable record of an executed trade (fill).
    One Order can produce multiple Trade records (partial fills).
    """

    __tablename__ = "trades"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy | sell
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False
    )
    executed_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )  # quantity * executed_price
    commission: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=4), nullable=False, default=Decimal("0")
    )  # 0.1% of total_value

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="trades")
    user: Mapped["User"] = relationship("User", back_populates="trades")

    def __repr__(self) -> str:
        return (
            f"<Trade {self.side.upper()} {self.quantity} {self.symbol} "
            f"@ {self.executed_price} commission={self.commission}>"
        )


class WatchlistItem(Base):
    """Stocks a user has saved to their watchlist."""

    __tablename__ = "watchlist_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="watchlist")

    def __repr__(self) -> str:
        return f"<WatchlistItem user={self.user_id} symbol={self.symbol}>"
