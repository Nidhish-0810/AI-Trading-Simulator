"""
SQLAlchemy ORM models for portfolio: Holding, Transaction, Achievement, Follower.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    average_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="holdings")  # type: ignore

    def __repr__(self) -> str:
        return f"<Holding user={self.user_id} {self.quantity} {self.symbol} @ {self.average_cost}>"


class Transaction(Base):
    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # buy | sell | deposit | commission
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(18, 6), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    balance_after: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="transactions")  # type: ignore

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} {self.symbol} ${self.total_amount}>"


class Achievement(Base):
    __tablename__ = "achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, name="metadata")

    user: Mapped["User"] = relationship("User", back_populates="achievements")  # type: ignore

    def __repr__(self) -> str:
        return f"<Achievement {self.achievement_type} user={self.user_id}>"


class Follower(Base):
    __tablename__ = "followers"

    follower_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    follower_user: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")  # type: ignore
    following_user: Mapped["User"] = relationship("User", foreign_keys=[following_id], back_populates="followers")  # type: ignore

    def __repr__(self) -> str:
        return f"<Follower {self.follower_id} -> {self.following_id}>"
