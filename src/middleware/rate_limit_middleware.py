"""
Rate limiting middleware using Redis.
Enforces rate limits per API key with sliding window algorithm.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.core.rate_limiter import RateLimiter
from src.dependencies import get_redis_client
from src.core.metrics import track_rate_limit

logger = logging.getLogger(__name__)

# Endpoints that don't require rate limiting
EXCLUDED_PATHS = [
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc"
]

# Default rate limit if not specified in API key
DEFAULT_RATE_LIMIT = 100
DEFAULT_WINDOW = 60  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware
    
    Enforces rate limits using Redis sliding window counter.
    Uses API key's rate_limit setting from database.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize rate limit middleware
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        logger.info("RateLimitMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check rate limit
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from next middleware/endpoint or 429 error
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            return await call_next(request)
        
        # Get API key data from request state (set by AuthMiddleware)
        api_key_data = getattr(request.state, "api_key", None)
        
        if not api_key_data:
            # No API key data - AuthMiddleware should have rejected this
            # Let it pass (fail open)
            logger.warning(
                "Rate limit check skipped - no API key data",
                extra={"path": request.url.path, "method": request.method}
            )
            return await call_next(request)
        
        try:
            # Get rate limit from API key or use default
            rate_limit = api_key_data.rate_limit or DEFAULT_RATE_LIMIT
            
            # Create rate limit key using API key ID
            rate_limit_key = f"rate_limit:{api_key_data.id}"
            
            # Get Redis client and rate limiter
            redis_client = get_redis_client()
            rate_limiter = RateLimiter(redis_client)
            
            # Check rate limit (synchronous call)
            allowed, remaining = rate_limiter.check_rate_limit(
                key=rate_limit_key,
                limit=rate_limit,
                window=DEFAULT_WINDOW
            )
            
            if not allowed:
                # Track rate limit hit with 0 remaining
                track_rate_limit(api_key_data.name, 0)

                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "key_name": api_key_data.name,
                        "key_id": api_key_data.id,
                        "rate_limit": rate_limit,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {rate_limit} requests per {DEFAULT_WINDOW} seconds."
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(DEFAULT_WINDOW)
                    }
                )
            
            # Track rate limit metrics
            track_rate_limit(api_key_data.name, remaining)

            logger.debug(
                "Rate limit check passed",
                extra={
                    "key_name": api_key_data.name,
                    "key_id": api_key_data.id,
                    "remaining": remaining,
                    "limit": rate_limit
                }
            )

            # Continue to next middleware/endpoint
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response
            
        except Exception as e:
            logger.error(
                "Error in rate limit middleware",
                extra={
                    "key_name": api_key_data.name if api_key_data else None,
                    "key_id": api_key_data.id if api_key_data else None,
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            # Fail open - allow request if rate limiting fails
            logger.warning("Rate limiting error - allowing request (fail open)")
            return await call_next(request)
