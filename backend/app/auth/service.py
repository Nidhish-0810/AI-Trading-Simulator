"""
Auth service: user registration, authentication, profile management.
"""
import logging
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserCreate, UpdateProfileRequest
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, schema: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == schema.email))
    if result.scalar_one_or_none():
        raise ValueError(f"Email '{schema.email}' is already registered")
    result = await db.execute(select(User).where(User.username == schema.username))
    if result.scalar_one_or_none():
        raise ValueError(f"Username '{schema.username}' is already taken")
    user = User(
        email=schema.email,
        username=schema.username,
        hashed_password=get_password_hash(schema.password),
        full_name=schema.full_name,
        balance=Decimal(str(settings.STARTING_BALANCE)),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info(f"New user registered: {user.username} ({user.email})")
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def update_user_profile(db: AsyncSession, user: User, schema: UpdateProfileRequest) -> User:
    update_data = schema.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_stats(db: AsyncSession, user: User) -> dict:
    from app.portfolio.models import Holding, Transaction
    from app.trading.models import Trade
    holdings_result = await db.execute(select(func.count(Holding.id)).where(Holding.user_id == user.id))
    total_trades_result = await db.execute(select(func.count(Trade.id)).where(Trade.user_id == user.id))
    buy_result = await db.execute(
        select(func.sum(Transaction.total_amount)).where(
            Transaction.user_id == user.id, Transaction.transaction_type == "buy"
        )
    )
    return {
        "holdings_count": holdings_result.scalar() or 0,
        "total_trades": total_trades_result.scalar() or 0,
        "total_invested": float(buy_result.scalar() or 0),
        "cash_balance": float(user.balance),
    }


async def get_all_users_for_leaderboard(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.created_at))
    return list(result.scalars().all())
