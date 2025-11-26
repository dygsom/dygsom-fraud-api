"""
Multi-layer cache system (L1 in-memory + L2 Redis).
Implements LRU cache for L1 and Redis for L2 with automatic fallback.
"""

from typing import Optional, Any, Dict
import json
import logging
import time
from redis import Redis
from src.core.config import settings
from src.core.metrics import track_cache

logger = logging.getLogger(__name__)


class CacheService:
    """
    Multi-layer cache service.
    
    L1: In-memory LRU cache (fastest, limited size)
    L2: Redis cache (fast, distributed)
    
    Attributes:
        redis_client: Redis connection
        l1_cache: In-memory LRU cache dict
        default_ttl: Default time-to-live in seconds
        l1_max_size: Maximum size of L1 cache
    """
    
    def __init__(
        self,
        redis_client: Redis,
        default_ttl: int = None,
        l1_max_size: int = None
    ):
        """Initialize cache service with L1 and L2

        Args:
            redis_client: Redis connection instance
            default_ttl: Default time-to-live in seconds (uses settings if None)
            l1_max_size: Maximum size of L1 cache (uses settings if None)
        """
        self.redis_client = redis_client
        self.l1_cache: Dict[str, Any] = {}
        self.default_ttl = default_ttl if default_ttl is not None else settings.CACHE_DEFAULT_TTL
        self.l1_max_size = l1_max_size if l1_max_size is not None else settings.CACHE_L1_MAX_SIZE
        
        logger.info(
            "CacheService initialized",
            extra={
                "default_ttl": default_ttl,
                "l1_max_size": l1_max_size
            }
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 → L2 → None).

        Try L1 first (fastest), then L2 (Redis), return None if miss.
        Log cache hits/misses with extra dict.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        start_time = time.time()

        try:
            # Try L1 cache first (fastest)
            if key in self.l1_cache:
                duration = time.time() - start_time
                track_cache("L1", "memory", hit=True, duration=duration)

                logger.debug(
                    "Cache hit",
                    extra={"key": key, "layer": "L1", "duration_ms": duration * 1000}
                )
                return self.l1_cache[key]

            # Try L2 (Redis) if L1 miss
            redis_value = self.redis_client.get(key)
            if redis_value is not None:
                # Deserialize from Redis
                value = self._deserialize(redis_value)

                # Populate L1 cache for next request
                self._set_l1(key, value)

                duration = time.time() - start_time
                track_cache("L2", "redis", hit=True, duration=duration)

                logger.debug(
                    "Cache hit",
                    extra={"key": key, "layer": "L2", "duration_ms": duration * 1000}
                )
                return value

            # Cache miss in both layers
            duration = time.time() - start_time
            track_cache("L2", "redis", hit=False, duration=duration)

            logger.debug(
                "Cache miss",
                extra={"key": key, "duration_ms": duration * 1000}
            )
            return None

        except Exception as e:
            duration = time.time() - start_time
            track_cache("L2", "redis", hit=False, duration=duration)

            logger.error(
                "Error getting from cache",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in both L1 and L2 cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized for Redis)
            ttl: Time-to-live in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl if ttl is not None else self.default_ttl
            
            # Set in L1 cache
            self._set_l1(key, value)
            
            # Serialize and set in L2 (Redis) with TTL
            serialized_value = self._serialize(value)
            self.redis_client.setex(key, ttl, serialized_value)
            
            logger.debug(
                "Cache set",
                extra={"key": key, "ttl": ttl}
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error setting cache",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from both L1 and L2.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted from at least one cache
        """
        try:
            deleted = False
            
            # Delete from L1
            if key in self.l1_cache:
                del self.l1_cache[key]
                deleted = True
            
            # Delete from L2 (Redis)
            if self.redis_client.delete(key) > 0:
                deleted = True
            
            if deleted:
                logger.debug(
                    "Cache key deleted",
                    extra={"key": key}
                )
            
            return deleted
            
        except Exception as e:
            logger.error(
                "Error deleting from cache",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def clear(self) -> bool:
        """Clear all caches (L1 and L2)
        
        Returns:
            True if successful
        """
        try:
            # Clear L1 cache
            self.l1_cache.clear()
            
            # Flush Redis (L2)
            self.redis_client.flushdb()
            
            logger.info("All caches cleared")
            return True
            
        except Exception as e:
            logger.error(
                "Error clearing caches",
                extra={"error": str(e)},
                exc_info=True
            )
            return False
    
    def _set_l1(self, key: str, value: Any) -> None:
        """Set value in L1 cache with size limit enforcement
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Enforce L1 cache size limit (simple FIFO eviction)
        if len(self.l1_cache) >= self.l1_max_size:
            # Remove oldest entry (first key in dict)
            oldest_key = next(iter(self.l1_cache))
            del self.l1_cache[oldest_key]
        
        self.l1_cache[key] = value
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string for Redis
        
        Args:
            value: Value to serialize
            
        Returns:
            JSON string
        """
        try:
            return json.dumps(value)
        except Exception as e:
            logger.error(
                "Error serializing value",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string from Redis
        
        Args:
            value: JSON string to deserialize
            
        Returns:
            Deserialized value
        """
        try:
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            return json.loads(value)
        except Exception as e:
            logger.error(
                "Error deserializing value",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
