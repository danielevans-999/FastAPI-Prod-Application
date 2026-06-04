import redis.asyncio as aioredis
import redis
from .config import settings

# Sync Redis client (for Celery, SlowAPI)
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

# Async Redis client (for FastAPI routes)
async def get_redis():
    client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
    try:
        yield client
    finally:
        await client.aclose()


async def cache_set(key: str, value: str, expire: int = 300):
    """Set cache with expiry in seconds"""
    await redis_client.setex(key, expire, value)


async def cache_get(key: str):
    """Get from cache"""
    return redis_client.get(key)


async def cache_delete(key: str):
    """Delete from cache"""
    redis_client.delete(key)


async def cache_delete_pattern(pattern: str):
    """Delete all keys matching pattern"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
