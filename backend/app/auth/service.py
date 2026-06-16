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
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, schema: UserCreate) -> User:
    """
    Create a new user account.

    Args:
        db: Database session
        schema: Registration data

    Returns:
        Created User model

    Raises:
        ValueError: If email or username is already taken
    """
    # Check for existing email
    result = await db.execute(select(User).where(User.email == schema.email))
    if result.scalar_one_or_none():
        raise ValueError(f"Email '{schema.email}' is already registered")

    # Check for existing username
    result = await db.execute(select(User).where(User.username == schema.username))
    if result.scalar_one_or_none():
        raise ValueError(f"Username '{schema.username}' is already taken")

    # Create user with starting balance
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
    await db.flush()  # Get the generated ID
    await db.refresh(user)

    logger.info(f"New user registered: {user.username} ({user.email})")
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """
    Verify email/password credentials.

    Returns:
        User if credentials are valid, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None

    return user


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Optional[User]:
    """Fetch a user by their UUID. Returns None if not found."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    """Fetch a user by email. Returns None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[User]:
    """Fetch a user by username. Returns None if not found."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession,
    user: User,
    schema: UpdateProfileRequest,
) -> User:
    """Update mutable profile fields."""
    update_data = schema.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


async def get_user_stats(
    db: AsyncSession,
    user: User,
) -> dict:
    """
    Compute quick user stats for profile display.
    Returns portfolio summary without live prices (for fast response).
    """
    from app.portfolio.models import Holding, Transaction
    from app.trading.models import Trade

    # Count holdings
    holdings_result = await db.execute(
        select(func.count(Holding.id)).where(Holding.user_id == user.id)
    )
    holdings_count = holdings_result.scalar() or 0

    # Count total trades
    trades_result = await db.execute(
        select(func.count(Trade.id)).where(Trade.user_id == user.id)
    )
    total_trades = trades_result.scalar() or 0

    # Compute total invested (sum of buy transactions)
    buy_result = await db.execute(
        select(func.sum(Transaction.total_amount)).where(
            Transaction.user_id == user.id,
            Transaction.type == "buy",
        )
    )
    total_invested = float(buy_result.scalar() or 0)

    return {
        "holdings_count": holdings_count,
        "total_trades": total_trades,
        "total_invested": total_invested,
        "cash_balance": float(user.balance),
    }


async def get_all_users_for_leaderboard(db: AsyncSession) -> list[User]:
    """Fetch all active users for leaderboard computation."""
    result = await db.execute(
        select(User).where(User.is_active == True).order_by(User.created_at)
    )
    return list(result.scalars().all())
