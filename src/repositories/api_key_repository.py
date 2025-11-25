"""
API Key Repository for managing API keys in the database.
Provides methods for CRUD operations and usage tracking.
"""

from typing import Optional, List
from datetime import datetime
import logging
from prisma import Prisma
from src.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ApiKeyRepository(BaseRepository):
    """Repository for API key management
    
    Handles database operations for API keys including creation,
    retrieval, usage tracking, and deactivation.
    """
    
    def __init__(self, prisma_client: Prisma):
        """Initialize API key repository
        
        Args:
            prisma_client: Prisma database client
        """
        # Note: Prisma generates model name as lowercase 'apikey'
        super().__init__(prisma_client, "apikey")
        logger.info("ApiKeyRepository initialized")
    
    async def find_by_key_hash(self, key_hash: str) -> Optional[dict]:
        """Find active API key by hash
        
        Only returns active keys that haven't expired.
        
        Args:
            key_hash: SHA-256 hash of the API key
            
        Returns:
            API key record if found and active, None otherwise
        """
        try:
            api_key = await self.prisma.apikey.find_first(
                where={
                    "key_hash": key_hash,
                    "is_active": True,
                    "OR": [
                        {"expires_at": None},
                        {"expires_at": {"gt": datetime.utcnow()}}
                    ]
                }
            )
            
            if api_key:
                logger.debug(
                    "API key found",
                    extra={"key_name": api_key.name, "key_id": api_key.id}
                )
            else:
                logger.debug(
                    "API key not found or inactive",
                    extra={"key_hash_prefix": key_hash[:8]}
                )
            
            return api_key
            
        except Exception as e:
            logger.error(
                "Error finding API key by hash",
                extra={"key_hash_prefix": key_hash[:8] if key_hash else None, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def create_api_key(
        self,
        key_hash: str,
        name: str,
        description: Optional[str] = None,
        rate_limit: int = 100,
        expires_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ) -> dict:
        """Create new API key
        
        Args:
            key_hash: SHA-256 hash of the API key
            name: Descriptive name for the key
            description: Optional description
            rate_limit: Requests per minute limit (default: 100)
            expires_at: Optional expiration datetime
            created_by: Optional creator identifier
            
        Returns:
            Created API key record
            
        Raises:
            Exception: If creation fails
        """
        try:
            api_key = await self.prisma.apikey.create(
                data={
                    "key_hash": key_hash,
                    "name": name,
                    "description": description,
                    "rate_limit": rate_limit,
                    "expires_at": expires_at,
                    "created_by": created_by
                }
            )
            
            logger.info(
                "API key created",
                extra={
                    "key_name": name,
                    "key_id": api_key.id,
                    "rate_limit": rate_limit
                }
            )
            
            return api_key
            
        except Exception as e:
            logger.error(
                "Error creating API key",
                extra={"name": name, "error": str(e)},
                exc_info=True
            )
            raise
    
    async def increment_request_count(self, key_id: str) -> bool:
        """Increment request count for API key
        
        Also updates last_used_at timestamp.
        
        Args:
            key_id: API key ID
            
        Returns:
            True if updated successfully
        """
        try:
            await self.prisma.apikey.update(
                where={"id": key_id},
                data={
                    "request_count": {"increment": 1},
                    "last_used_at": datetime.utcnow()
                }
            )
            
            logger.debug(
                "API key request count incremented",
                extra={"key_id": key_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error incrementing request count",
                extra={"key_id": key_id, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def deactivate_key(self, key_id: str) -> bool:
        """Deactivate API key
        
        Args:
            key_id: API key ID
            
        Returns:
            True if deactivated successfully
        """
        try:
            await self.prisma.apikey.update(
                where={"id": key_id},
                data={"is_active": False}
            )
            
            logger.info(
                "API key deactivated",
                extra={"key_id": key_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error deactivating API key",
                extra={"key_id": key_id, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def get_active_keys(self) -> List[dict]:
        """Get all active API keys
        
        Returns:
            List of active API key records
        """
        try:
            api_keys = await self.prisma.apikey.find_many(
                where={"is_active": True},
                order={"created_at": "desc"}
            )
            
            logger.debug(
                "Active API keys retrieved",
                extra={"count": len(api_keys)}
            )
            
            return api_keys
            
        except Exception as e:
            logger.error(
                "Error getting active API keys",
                extra={"error": str(e)},
                exc_info=True
            )
            return []
    
    async def find_by_id(self, key_id: str) -> Optional[dict]:
        """Find API key by ID
        
        Args:
            key_id: API key ID
            
        Returns:
            API key record if found, None otherwise
        """
        try:
            api_key = await self.prisma.apikey.find_unique(
                where={"id": key_id}
            )
            
            if api_key:
                logger.debug(
                    "API key found by ID",
                    extra={"key_id": key_id, "key_name": api_key.name}
                )
            
            return api_key
            
        except Exception as e:
            logger.error(
                "Error finding API key by ID",
                extra={"key_id": key_id, "error": str(e)},
                exc_info=True
            )
            return None
