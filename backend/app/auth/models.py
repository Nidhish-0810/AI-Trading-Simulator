"""
User model for authentication and profile management.
"""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.trading.models import Order, Trade, WatchlistItem
    from app.portfolio.models import Holding, Transaction, Achievement, Follower
    from app.notifications.models import PriceAlert, Notification


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=Decimal("100000.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    trades: Mapped[List["Trade"]] = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    holdings: Mapped[List["Holding"]] = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[List["Achievement"]] = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    watchlist: Mapped[List["WatchlistItem"]] = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    price_alerts: Mapped[List["PriceAlert"]] = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    followers: Mapped[List["Follower"]] = relationship("Follower", foreign_keys="[Follower.following_id]", back_populates="following_user", cascade="all, delete-orphan")
    following: Mapped[List["Follower"]] = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower_user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} balance={self.balance}>"
