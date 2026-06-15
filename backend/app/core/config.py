"""
Application configuration using Pydantic Settings.
"""
import logging
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    APP_NAME: str = "TradeAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "change-me-in-production-at-least-32-characters-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://tradeai:tradeai_secret_2024@localhost:5432/tradeai_db"
    REDIS_URL: str = "redis://:redis_secret_2024@localhost:6379/0"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError(f"SECRET_KEY must be at least 32 characters (got {len(v)})")
        if v in ("change-me-in-production-at-least-32-characters-long",
                 "your-super-secret-key-change-this-in-production-min-32-chars"):
            import os
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("Cannot use default SECRET_KEY in production!")
            logger.warning("Using default SECRET_KEY in development mode. Never use in production!")
        return v

    STARTING_BALANCE: float = 100_000.0
    COMMISSION_RATE: float = 0.001
    MIN_ORDER_VALUE: float = 1.0
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10
    MARKET_DATA_CACHE_TTL: int = 60
    HISTORY_CACHE_TTL: int = 300
    NEWS_CACHE_TTL: int = 600
    PORTFOLIO_CACHE_TTL: int = 30
    AI_SIGNAL_CACHE_TTL: int = 300
    BACKTEST_MAX_YEARS: int = 5

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
