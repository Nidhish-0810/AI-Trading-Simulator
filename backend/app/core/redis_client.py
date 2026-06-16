"""
Redis client: connection pool, caching helpers, and pub/sub utilities.
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Global Pool ─────────────────────────────────────────────────────────────
_redis_pool: Optional[Redis] = None


async def get_redis_pool() -> Redis:
    """Initialize and return the Redis connection pool (singleton)."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("Redis connection pool initialized")
    return _redis_pool


async def close_redis_pool() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("Redis connection pool closed")


async def get_redis() -> Redis:
    """FastAPI dependency that returns the Redis client."""
    return await get_redis_pool()


# ─── Cache Helpers ────────────────────────────────────────────────────────────
async def get_cache(redis: Redis, key: str) -> Optional[Any]:
    """Get a cached value (auto-deserializes JSON)."""
    try:
        value = await redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache GET error for key {key}: {e}")
        return None


async def set_cache(redis: Redis, key: str, value: Any, ttl: int = 60) -> bool:
    """Set a cache value with TTL (auto-serializes to JSON)."""
    try:
        serialized = json.dumps(value, default=str)
        await redis.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Cache SET error for key {key}: {e}")
        return False


async def delete_cache(redis: Redis, key: str) -> bool:
    """Delete a cache key."""
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache DELETE error for key {key}: {e}")
        return False


async def delete_pattern(redis: Redis, pattern: str) -> int:
    """Delete all keys matching a pattern. Returns count of deleted keys."""
    try:
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache DELETE PATTERN error for {pattern}: {e}")
        return 0


# ─── Pub/Sub Helpers ──────────────────────────────────────────────────────────
async def publish(redis: Redis, channel: str, message: Any) -> int:
    """Publish a message to a Redis channel."""
    try:
        serialized = json.dumps(message, default=str)
        return await redis.publish(channel, serialized)
    except Exception as e:
        logger.error(f"Redis PUBLISH error on channel {channel}: {e}")
        return 0


async def get_pubsub(redis: Redis) -> aioredis.client.PubSub:
    """Create a new pub/sub connection."""
    return redis.pubsub()


# ─── Cache Key Builders ───────────────────────────────────────────────────────
class CacheKeys:
    """Centralized cache key namespace."""

    @staticmethod
    def stock_quote(symbol: str) -> str:
        return f"quote:{symbol.upper()}"

    @staticmethod
    def stock_history(symbol: str, period: str, interval: str) -> str:
        return f"history:{symbol.upper()}:{period}:{interval}"

    @staticmethod
    def stock_news(symbol: str) -> str:
        return f"news:{symbol.upper()}"

    @staticmethod
    def market_summary() -> str:
        return "market:summary"

    @staticmethod
    def trending() -> str:
        return "market:trending"

    @staticmethod
    def portfolio(user_id: str) -> str:
        return f"portfolio:{user_id}"

    @staticmethod
    def portfolio_analytics(user_id: str) -> str:
        return f"analytics:{user_id}"

    @staticmethod
    def ai_signals(symbol: str) -> str:
        return f"ai:signals:{symbol.upper()}"

    @staticmethod
    def leaderboard(period: str = "all") -> str:
        return f"leaderboard:{period}"

    @staticmethod
    def price_channel(symbol: str) -> str:
        return f"prices:{symbol.upper()}"

    @staticmethod
    def user_notifications(user_id: str) -> str:
        return f"notifications:{user_id}"
