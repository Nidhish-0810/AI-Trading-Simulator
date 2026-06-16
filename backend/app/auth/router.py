"""
Auth router: registration, login, token refresh, profile endpoints.
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.models import User
from app.auth.schemas import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserCreate,
    UserLogin,
    UserProfile,
    UserResponse,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
    verify_token,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    schema: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **username**: 3-50 chars, alphanumeric + underscore/dash (unique)
    - **password**: Min 8 chars, must contain uppercase and digit
    - **full_name**: Optional display name

    Returns JWT access + refresh tokens immediately after registration.
    New account starts with $100,000 virtual balance.
    """
    try:
        user = await auth_service.register_user(db, schema)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Issue tokens immediately
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT tokens",
)
async def login(
    schema: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email and password.

    Returns:
    - **access_token**: Short-lived JWT (30 min default)
    - **refresh_token**: Long-lived JWT for token rotation (7 days)
    - **user**: Current user data
    """
    user = await auth_service.authenticate_user(db, schema.email, schema.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    schema: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Use a refresh token to get a new access token.
    The refresh token remains valid until it expires (7 days).
    """
    payload = verify_token(schema.refresh_token, token_type="refresh")
    user_id_str = payload.get("sub")

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = await auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout")
async def logout(current_user: User = Depends(get_current_active_user)) -> None:
    """
    Logout endpoint. Client should discard tokens locally.
    (Stateless JWT — no server-side blacklist in this implementation.)
    """
    logger.info(f"User logged out: {current_user.username}")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Get the authenticated user's full profile with stats."""
    stats = await auth_service.get_user_stats(db, current_user)

    profile = UserProfile.model_validate(current_user)
    profile.total_trades = stats["total_trades"]
    return profile


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
)
async def update_profile(
    schema: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update mutable profile fields: full_name, bio, avatar_url."""
    updated_user = await auth_service.update_user_profile(db, current_user, schema)
    return UserResponse.model_validate(updated_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password(
    schema: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change the current user's password."""
    if not verify_password(schema.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = get_password_hash(schema.new_password)
    await db.flush()
    logger.info(f"Password changed for user: {current_user.username}")
