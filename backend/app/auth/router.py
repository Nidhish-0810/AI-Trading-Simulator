"""
Auth router: registration, login, token refresh, profile endpoints.
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.models import User
from app.auth.schemas import (ChangePasswordRequest, RefreshTokenRequest, TokenResponse, UpdateProfileRequest, UserCreate, UserLogin, UserProfile, UserResponse)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (create_access_token, create_refresh_token, get_current_active_user, get_password_hash, verify_password, verify_token)

import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(schema: UserCreate, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        user = await auth_service.register_user(db, schema)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(schema: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await auth_service.authenticate_user(db, schema.email, schema.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(schema: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    payload = verify_token(schema.refresh_token, token_type="refresh")
    try:
        user_id = uuid.UUID(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = await auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or deactivated")
    new_access = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: User = Depends(get_current_active_user)) -> None:
    logger.info(f"User logged out: {current_user.username}")


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> UserProfile:
    stats = await auth_service.get_user_stats(db, current_user)
    profile = UserProfile.model_validate(current_user)
    profile.total_trades = stats["total_trades"]
    return profile


@router.put("/profile", response_model=UserResponse)
async def update_profile(schema: UpdateProfileRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> UserResponse:
    updated_user = await auth_service.update_user_profile(db, current_user, schema)
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(schema: ChangePasswordRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> None:
    if not verify_password(schema.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(schema.new_password)
    await db.flush()
