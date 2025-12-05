"""
Authentication middleware for API key validation.
Validates X-API-Key header on all requests (except health/docs endpoints).
"""

import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.core.security import SecurityUtils
from src.repositories.api_key_repository import ApiKeyRepository
from src.dependencies import get_prisma

logger = logging.getLogger(__name__)

# Endpoints that don't require authentication
EXCLUDED_PATHS = [
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
    "/api/v1/auth/",     # Auth endpoints (signup, login, etc.)
    "/api/v1/dashboard/" # Dashboard endpoints use JWT token, not API Key
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware
    
    Validates API keys for all requests except excluded paths.
    Stores API key data in request.state for use in endpoints.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize authentication middleware
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        logger.info("AuthMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate API key
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from next middleware/endpoint or 401 error
        """
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            logger.warning(
                "Missing API key",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing API key. Include X-API-Key header in your request."
                }
            )
        
        try:
            # Hash the API key
            key_hash = SecurityUtils.hash_api_key(api_key)
            
            # Get Prisma client and repository
            prisma = await get_prisma()
            api_key_repo = ApiKeyRepository(prisma)
            
            # Find API key in database
            api_key_data = await api_key_repo.find_by_key_hash(key_hash)
            
            if not api_key_data:
                logger.warning(
                    "Invalid API key",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "key_prefix": api_key[:12] if api_key else None
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid API key"
                    }
                )
            
            # Store API key data in request state
            request.state.api_key = api_key_data
            
            # Increment request count (async, don't wait)
            await api_key_repo.increment_request_count(api_key_data.id)
            
            logger.info(
                "API key authenticated",
                extra={
                    "key_name": api_key_data.name,
                    "key_id": api_key_data.id,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            # Continue to next middleware/endpoint
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(
                "Error in authentication middleware",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal authentication error"
                }
            )
