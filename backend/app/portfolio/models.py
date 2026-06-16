"""
SQLAlchemy ORM models for portfolio management: Holding, Transaction,
Achievement, and Follower (social graph).
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class Holding(Base):
    """
    Represents the current position a user holds in a particular stock.

    average_cost is the volume-weighted average purchase price.
    """

    __tablename__ = "holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    average_cost: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, comment="Volume-weighted average cost per share"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="holdings")  # type: ignore

    def __repr__(self) -> str:
        return f"<Holding user={self.user_id} {self.quantity} {self.symbol} @ {self.average_cost}>"


class Transaction(Base):
    """Immutable ledger entry recording every financial event in the simulator."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum"), nullable=False
    )
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(18, 6), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="transactions")  # type: ignore

    def __repr__(self) -> str:
        return f"<Transaction {self.type} {self.symbol} ${self.total_amount}>"


class Achievement(Base):
    """Gamification achievement earned by a user."""

    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, name="metadata"
    )

    user: Mapped["User"] = relationship("User", back_populates="achievements")  # type: ignore

    def __repr__(self) -> str:
        return f"<Achievement {self.achievement_type} user={self.user_id}>"


class Follower(Base):
    """Social graph edge: follower_id follows following_id."""

    __tablename__ = "followers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    follower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    follower_user: Mapped["User"] = relationship(  # type: ignore
        "User", foreign_keys=[follower_id], back_populates="following"
    )
    following_user: Mapped["User"] = relationship(  # type: ignore
        "User", foreign_keys=[following_id], back_populates="followers"
    )

    def __repr__(self) -> str:
        return f"<Follower {self.follower_id} -> {self.following_id}>"
