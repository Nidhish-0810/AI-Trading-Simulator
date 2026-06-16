"""
Notifications models: PriceAlert and Notification.
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)  # above | below
    target_price: Mapped[float] = mapped_column(nullable=False)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="price_alerts")


class Notification(Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    related_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")
