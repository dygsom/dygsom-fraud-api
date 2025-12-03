"""
Dependency injection for FastAPI.
Provides instances of services and repositories with proper initialization.
"""

import os
from redis import Redis
from prisma import Prisma
from fastapi import HTTPException, Header, status
import jwt
from typing import Optional

from src.services.fraud_service import FraudService
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.cache_repository import CacheRepository
from src.core.cache import CacheService
from src.core.config import settings
from src.ml.ml_service import MLService
import logging

logger = logging.getLogger(__name__)

# Global Prisma client instance
# In production, this should be managed with proper lifecycle
_prisma_client = None

# Global Redis client instance
_redis_client = None


async def get_prisma() -> Prisma:
    """Get Prisma client instance

    Creates and connects Prisma client if not already connected.

    Returns:
        Connected Prisma client instance

    Raises:
        Exception: If Prisma connection fails
    """
    global _prisma_client

    if _prisma_client is None:
        logger.info("Initializing Prisma client")
        _prisma_client = Prisma()
        await _prisma_client.connect()
        logger.info("Prisma client connected successfully")

    return _prisma_client


def get_redis_client() -> Redis:
    """Get Redis client instance
    
    Creates Redis client if not already created.
    Connects to Redis using REDIS_URL environment variable.
    
    Returns:
        Redis client instance
    
    Raises:
        Exception: If Redis connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        # Get Redis URL from environment or use default
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        logger.info(
            "Initializing Redis client",
            extra={"redis_url": redis_url}
        )
        
        # Create Redis client
        _redis_client = Redis.from_url(
            redis_url,
            decode_responses=False,  # We'll handle decoding in CacheService
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        try:
            _redis_client.ping()
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error(
                "Failed to connect to Redis",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    return _redis_client


def get_cache_service() -> CacheService:
    """Get CacheService instance
    
    Creates CacheService with Redis connection.
    
    Returns:
        Initialized CacheService with Redis connection
    """
    redis_client = get_redis_client()
    cache_service = CacheService(redis_client)
    return cache_service


async def get_fraud_service() -> FraudService:
    """Get FraudService instance with dependencies

    Dependency injection for FraudService.
    Creates all required dependencies (Prisma, Repository, CacheRepository, MLService).

    Returns:
        FraudService instance ready to use

    Raises:
        Exception: If service initialization fails
    """
    try:
        logger.debug("Initializing FraudService dependencies")

        # Get Prisma client
        prisma_client = await get_prisma()

        # Initialize transaction repository
        transaction_repository = TransactionRepository(prisma_client)
        
        # Initialize cache service and repository
        cache_service = get_cache_service()
        cache_repository = CacheRepository(cache_service)

        # Initialize FraudService with cache support
        fraud_service = FraudService(
            transaction_repo=transaction_repository,
            cache_repo=cache_repository
        )

        logger.debug("FraudService dependencies initialized successfully")

        return fraud_service

    except Exception as e:
        logger.error(
            "Failed to initialize FraudService",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.

    Extracts and validates JWT token from Authorization header.
    Returns user payload if token is valid.

    Args:
        authorization: Authorization header (format: "Bearer <token>")

    Returns:
        Dictionary with user information from JWT payload:
        {
            "user_id": str,
            "email": str,
            "organization_id": str,
            "role": str
        }

    Raises:
        HTTPException 401: If token is missing, invalid, or expired

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user["user_id"]
            ...
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()

        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"}
            )

        scheme, token = parts

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Expected: Bearer",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )

        # Validate required fields
        required_fields = ["user_id", "email"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: missing {field}",
                    headers={"WWW-Authenticate": "Bearer"}
                )

        logger.debug(f"User authenticated: {payload.get('email')}")

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )
