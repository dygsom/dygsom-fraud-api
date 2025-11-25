"""
Admin endpoints for API key management.
Requires authentication - all endpoints protected by AuthMiddleware.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from src.repositories.api_key_repository import ApiKeyRepository
from src.core.security import SecurityUtils
from src.dependencies import get_prisma

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/api-keys",
    tags=["Admin - API Keys"]
)


# DTOs
class CreateApiKeyRequest(BaseModel):
    """Request to create new API key"""
    name: str = Field(..., description="Name for the API key", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description of the API key purpose", max_length=500)
    rate_limit: int = Field(100, description="Requests per minute", ge=1, le=10000)
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp (null = never expires)")
    created_by: Optional[str] = Field(None, description="User/system that created the key", max_length=100)
    
    @validator("expires_at")
    def validate_expires_at(cls, v):
        """Validate expiration is in the future"""
        if v is not None and v <= datetime.utcnow():
            raise ValueError("expires_at must be in the future")
        return v


class ApiKeyResponse(BaseModel):
    """Response with API key details"""
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    rate_limit: int
    request_count: int
    last_used_at: Optional[datetime]
    created_by: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Only returned when creating new key
    api_key: Optional[str] = Field(None, description="Plain text API key (only shown once)")


class ApiKeyListResponse(BaseModel):
    """Response with list of API keys"""
    keys: List[ApiKeyResponse]
    total: int


# Endpoints
@router.post(
    "",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new API key",
    description="Creates a new API key and returns it. **Warning:** The plain text key is only shown once!"
)
async def create_api_key(
    request: CreateApiKeyRequest,
    prisma=Depends(get_prisma)
):
    """Create new API key
    
    Args:
        request: API key creation request
        prisma: Prisma client
        
    Returns:
        ApiKeyResponse with plain text API key (only time it's shown)
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(
            "Creating new API key",
            extra={
                "name": request.name,
                "rate_limit": request.rate_limit,
                "created_by": request.created_by
            }
        )
        
        # Generate API key and hash
        plain_key, key_hash = SecurityUtils.generate_and_hash()
        
        # Create repository
        api_key_repo = ApiKeyRepository(prisma)
        
        # Create API key in database
        api_key_data = await api_key_repo.create_api_key(
            key_hash=key_hash,
            name=request.name,
            description=request.description,
            rate_limit=request.rate_limit,
            expires_at=request.expires_at,
            created_by=request.created_by
        )
        
        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
        
        logger.info(
            "API key created successfully",
            extra={
                "key_id": api_key_data.id,
                "name": api_key_data.name
            }
        )
        
        # Return response with plain text key (only time it's shown)
        return ApiKeyResponse(
            id=api_key_data.id,
            name=api_key_data.name,
            description=api_key_data.description,
            is_active=api_key_data.is_active,
            rate_limit=api_key_data.rate_limit,
            request_count=api_key_data.request_count,
            last_used_at=api_key_data.last_used_at,
            created_by=api_key_data.created_by,
            expires_at=api_key_data.expires_at,
            created_at=api_key_data.created_at,
            updated_at=api_key_data.updated_at,
            api_key=plain_key  # ONLY shown here!
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating API key",
            extra={
                "name": request.name,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="List all active API keys",
    description="Returns all active API keys (plain text keys never returned)"
)
async def list_api_keys(
    prisma=Depends(get_prisma)
):
    """List all active API keys
    
    Args:
        prisma: Prisma client
        
    Returns:
        ApiKeyListResponse with list of keys
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        logger.info("Listing API keys")
        
        # Create repository
        api_key_repo = ApiKeyRepository(prisma)
        
        # Get active keys
        keys = await api_key_repo.get_active_keys()
        
        logger.info(
            "API keys listed successfully",
            extra={"count": len(keys)}
        )
        
        # Convert to response models
        key_responses = [
            ApiKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                is_active=key.is_active,
                rate_limit=key.rate_limit,
                request_count=key.request_count,
                last_used_at=key.last_used_at,
                created_by=key.created_by,
                expires_at=key.expires_at,
                created_at=key.created_at,
                updated_at=key.updated_at,
                api_key=None  # Never return plain text key
            )
            for key in keys
        ]
        
        return ApiKeyListResponse(
            keys=key_responses,
            total=len(key_responses)
        )
        
    except Exception as e:
        logger.error(
            "Error listing API keys",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate API key",
    description="Deactivates an API key (soft delete - sets is_active=false)"
)
async def deactivate_api_key(
    key_id: str,
    prisma=Depends(get_prisma)
):
    """Deactivate API key
    
    Args:
        key_id: API key ID to deactivate
        prisma: Prisma client
        
    Returns:
        204 No Content
        
    Raises:
        HTTPException: If key not found or deactivation fails
    """
    try:
        logger.info(
            "Deactivating API key",
            extra={"key_id": key_id}
        )
        
        # Create repository
        api_key_repo = ApiKeyRepository(prisma)
        
        # Check key exists
        existing_key = await api_key_repo.find_by_id(key_id)
        if not existing_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}"
            )
        
        # Deactivate key
        success = await api_key_repo.deactivate_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate API key"
            )
        
        logger.info(
            "API key deactivated successfully",
            extra={
                "key_id": key_id,
                "name": existing_key.name
            }
        )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deactivating API key",
            extra={
                "key_id": key_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate API key: {str(e)}"
        )
