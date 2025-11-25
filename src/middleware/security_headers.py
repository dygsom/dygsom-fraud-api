"""
Security headers middleware.
Adds security-related HTTP headers to all responses.
"""

import logging
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware
    
    Adds standard security headers to all responses:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - X-Request-ID: Track requests across services
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize security headers middleware
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        logger.info("SecurityHeadersMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response with security headers added
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Store request ID in request state for logging
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["X-Request-ID"] = request_id
            
            # Add custom headers for debugging (in non-production)
            response.headers["X-API-Version"] = "1.0.0"
            
            logger.debug(
                "Security headers added",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Error in security headers middleware",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
