"""
Pydantic schemas for authentication and user management.
"""
import uuid
from decimal import Decimal
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ─── Request Schemas ─────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        reserved = {"admin", "root", "system", "tradeai", "support"}
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved")
        return v.lower()


class UserLogin(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    """Schema for profile update."""
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)


class ChangePasswordRequest(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ─── Response Schemas ────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Public user data returned in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    balance: Decimal
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserProfile(BaseModel):
    """Extended user profile with stats."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    balance: Decimal
    is_active: bool
    created_at: datetime

    # Stats (computed, not from DB)
    portfolio_value: float = 0.0
    total_invested: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    rank: Optional[int] = None
    followers_count: int = 0
    following_count: int = 0


class TokenResponse(BaseModel):
    """JWT token pair returned on login/refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    user: UserResponse


class PublicUserProfile(BaseModel):
    """Minimal public profile (for leaderboard, social features)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    # Public stats
    total_return_pct: float = 0.0
    total_trades: int = 0
    rank: Optional[int] = None
