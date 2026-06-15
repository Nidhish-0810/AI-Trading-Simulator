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
_redis_pool: Optional[Redis] = None


async def get_redis_pool() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True, max_connections=20
        )
    return _redis_pool


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


async def get_redis() -> Redis:
    return await get_redis_pool()


async def get_cache(redis: Redis, key: str) -> Optional[Any]:
    try:
        value = await redis.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning(f"Cache GET error {key}: {e}")
        return None


async def set_cache(redis: Redis, key: str, value: Any, ttl: int = 60) -> bool:
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache SET error {key}: {e}")
        return False


async def delete_cache(redis: Redis, key: str) -> bool:
    try:
        await redis.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache DELETE error {key}: {e}")
        return False


async def delete_pattern(redis: Redis, pattern: str) -> int:
    try:
        keys = await redis.keys(pattern)
        return await redis.delete(*keys) if keys else 0
    except Exception as e:
        logger.warning(f"Cache DELETE PATTERN error {pattern}: {e}")
        return 0


async def publish(redis: Redis, channel: str, message: Any) -> int:
    try:
        return await redis.publish(channel, json.dumps(message, default=str))
    except Exception as e:
        logger.error(f"Redis PUBLISH error {channel}: {e}")
        return 0


class CacheKeys:
    @staticmethod
    def stock_quote(symbol: str) -> str: return f"quote:{symbol.upper()}"
    @staticmethod
    def stock_history(symbol: str, period: str, interval: str) -> str: return f"history:{symbol.upper()}:{period}:{interval}"
    @staticmethod
    def stock_news(symbol: str) -> str: return f"news:{symbol.upper()}"
    @staticmethod
    def market_summary() -> str: return "market:summary"
    @staticmethod
    def trending() -> str: return "market:trending"
    @staticmethod
    def portfolio(user_id: str) -> str: return f"portfolio:{user_id}"
    @staticmethod
    def ai_signals(symbol: str) -> str: return f"ai:signals:{symbol.upper()}"
    @staticmethod
    def leaderboard(period: str = "all") -> str: return f"leaderboard:{period}"
    @staticmethod
    def price_channel(symbol: str) -> str: return f"prices:{symbol.upper()}"
