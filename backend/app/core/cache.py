import redis
import json
from typing import Any, Optional
from functools import wraps
from app.config.logging import logger
from app.config.settings import settings


class CacheService:
    """Redis-based caching service with graceful failure handling"""

    def __init__(self, host: str = None, port: int = None, db: int = None):
        """
        Initialize Redis cache client.

        Args:
            host: Redis server hostname (defaults to settings.redis_host)
            port: Redis server port (defaults to settings.redis_port)
            db: Redis database number (defaults to settings.redis_db)
        """
        # Use settings if parameters not provided
        host = host or settings.redis_host
        port = port or settings.redis_port
        db = db if db is not None else settings.redis_db

        # Check if caching is enabled
        if not settings.cache_enabled:
            self.redis_client = None
            self.available = False
            logger.info("Redis caching disabled via settings (CACHE_ENABLED=False)")
            return

        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info(f"Redis cache connected successfully at {host}:{port} (db={db})")
        except (redis.RedisError, ConnectionError) as e:
            self.redis_client = None
            self.available = False
            logger.warning(f"Redis cache unavailable: {e}. Caching will be disabled.")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or cache unavailable
        """
        if not self.available:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.debug(f"Cache get error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
        """
        if not self.available:
            return

        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: key='{key}', ttl={ttl}s")
        except (redis.RedisError, TypeError, ValueError) as e:
            logger.debug(f"Cache set error for key '{key}': {e}")

    def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key to delete
        """
        if not self.available:
            return

        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted: key='{key}'")
        except redis.RedisError as e:
            logger.debug(f"Cache delete error for key '{key}': {e}")

    def delete_pattern(self, pattern: str):
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (supports * wildcards)
        """
        if not self.available:
            return

        try:
            deleted_count = 0
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
                deleted_count += 1
            logger.debug(f"Cache pattern deleted: pattern='{pattern}', count={deleted_count}")
        except redis.RedisError as e:
            logger.debug(f"Cache pattern delete error for pattern '{pattern}': {e}")

    def clear_all(self):
        """Clear all keys in the current database (use with caution)"""
        if not self.available:
            return

        try:
            self.redis_client.flushdb()
            logger.info("Cache cleared (flushdb)")
        except redis.RedisError as e:
            logger.error(f"Cache clear error: {e}")


# Global cache instance (initialized with default settings)
cache = CacheService()


def cached(ttl: int = 60, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=30, key_prefix="network")
        async def get_network_summary():
            return {"devices": 10}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
