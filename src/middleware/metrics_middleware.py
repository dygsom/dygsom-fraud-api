"""
Metrics middleware for automatic request tracking.
Captures request duration, status code, and API key for all requests.
"""

import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.metrics import track_request

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track request metrics.
    
    Tracks:
    - Request count per endpoint
    - Request duration
    - Status codes
    - API key usage
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        start_time = time.time()
        
        # Extract API key name from headers (if present)
        api_key_header = request.headers.get("X-API-Key", "")
        api_key_name = self._extract_api_key_name(api_key_header)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Track metrics
        track_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration,
            api_key_name=api_key_name,
        )
        
        logger.debug(
            "Request processed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration * 1000,
                "api_key_name": api_key_name,
            },
        )
        
        return response

    def _extract_api_key_name(self, api_key: str) -> str:
        """
        Extract API key name from full key.
        
        Args:
            api_key: Full API key string
            
        Returns:
            API key name or 'unknown'
        """
        if not api_key:
            return "unknown"
        
        # Extract prefix (e.g., "dygsom_live_" -> "dygsom_live")
        if "_" in api_key:
            parts = api_key.split("_")
            if len(parts) >= 2:
                return f"{parts[0]}_{parts[1]}"
        
        return "unknown"
