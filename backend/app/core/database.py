"""
Async SQLAlchemy database engine, session factory, and base model.
"""
import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG,
    pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession,
    expire_on_commit=False, autocommit=False, autoflush=False,
)


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    from app.auth.models import User  # noqa
    from app.trading.models import Order, Trade, WatchlistItem  # noqa
    from app.portfolio.models import Holding, Transaction, Achievement, Follower  # noqa
    from app.notifications.models import PriceAlert, Notification  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
