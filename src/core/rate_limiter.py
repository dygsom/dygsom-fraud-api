"""
Rate limiter implementation using Redis.
Implements sliding window counter for rate limiting.
"""

import time
import logging
from typing import Tuple
from redis import Redis
from src.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis sliding window counter
    
    Implements rate limiting with Redis to track request counts
    across multiple API instances.
    """
    
    def __init__(self, redis_client: Redis):
        """Initialize rate limiter
        
        Args:
            redis_client: Redis connection instance
        """
        self.redis = redis_client
        logger.info("RateLimiter initialized")
    
    def check_rate_limit(
        self,
        key: str,
        limit: int = None,
        window: int = None
    ) -> Tuple[bool, int]:
        """Check if request is within rate limit

        Implements sliding window counter algorithm:
        1. Get current count for the window
        2. If count >= limit, deny request
        3. If count < limit, increment and allow

        Args:
            key: Unique identifier for rate limit (e.g., api_key, ip_address)
            limit: Maximum number of requests allowed in window (uses settings if None)
            window: Time window in seconds (uses settings if None)

        Returns:
            Tuple of (allowed: bool, remaining: int)
            - allowed: True if request is within limit
            - remaining: Number of requests remaining in current window
        """
        # Use settings defaults if not provided
        if limit is None:
            limit = settings.RATE_LIMIT_PER_MINUTE
        if window is None:
            window = settings.RATE_LIMIT_WINDOW_SECONDS

        try:
            # Generate Redis key with timestamp bucket
            current_time = int(time.time())
            window_start = current_time - window
            redis_key = f"rate_limit:{key}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(redis_key)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                remaining = 0
                allowed = False
                
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "key": key,
                        "current_count": current_count,
                        "limit": limit
                    }
                )
            else:
                # Add current request to sorted set
                self.redis.zadd(redis_key, {str(current_time): current_time})
                
                # Set expiry on key (window + buffer)
                self.redis.expire(redis_key, window + 10)
                
                remaining = limit - current_count - 1
                allowed = True
                
                logger.debug(
                    "Rate limit check passed",
                    extra={
                        "key": key,
                        "current_count": current_count + 1,
                        "remaining": remaining,
                        "limit": limit
                    }
                )
            
            return allowed, remaining
            
        except Exception as e:
            logger.error(
                "Error checking rate limit",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            # On error, allow request (fail open)
            return True, limit
    
    def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit counter for a key
        
        Useful for testing or administrative overrides.
        
        Args:
            key: Unique identifier for rate limit
            
        Returns:
            True if reset successfully
        """
        try:
            redis_key = f"rate_limit:{key}"
            self.redis.delete(redis_key)
            
            logger.info(
                "Rate limit reset",
                extra={"key": key}
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error resetting rate limit",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            return False
    
    def get_current_usage(self, key: str) -> int:
        """Get current request count for a key
        
        Args:
            key: Unique identifier for rate limit
            
        Returns:
            Current number of requests in window
        """
        try:
            redis_key = f"rate_limit:{key}"
            count = self.redis.zcard(redis_key)
            
            logger.debug(
                "Rate limit usage retrieved",
                extra={"key": key, "count": count}
            )
            
            return count
            
        except Exception as e:
            logger.error(
                "Error getting rate limit usage",
                extra={"key": key, "error": str(e)},
                exc_info=True
            )
            return 0
