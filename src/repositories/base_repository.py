"""
Base repository with common CRUD operations.
Implements Repository Pattern with type-safe CRUD operations.
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from prisma import Prisma
import logging

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Base repository for common CRUD operations

    This is an abstract base class that provides common database operations.
    Subclasses should specify the model name and implement model-specific logic.
    """

    def __init__(self, prisma: Prisma, model_name: str):
        """Initialize repository

        Args:
            prisma: Prisma client instance
            model_name: Name of the Prisma model (e.g., 'transaction', 'fraud_features')
        """
        self.prisma = prisma
        self.model_name = model_name
        self._model = getattr(prisma, model_name)

    async def find_by_id(self, id: str) -> Optional[Dict[Any, Any]]:
        """Find entity by ID

        Args:
            id: Entity ID

        Returns:
            Entity dict if found, None otherwise

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Finding {self.model_name} by id: {id}")
            result = await self._model.find_unique(where={"id": id})
            return result
        except Exception as e:
            logger.error(f"Error finding {self.model_name} by id {id}: {str(e)}")
            raise

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Dict[Any, Any]]:
        """Find all entities with pagination

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            List of entity dicts

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Finding all {self.model_name} (skip={skip}, limit={limit})")
            results = await self._model.find_many(
                skip=skip, take=limit, order={"created_at": "desc"}
            )
            return results
        except Exception as e:
            logger.error(f"Error finding all {self.model_name}: {str(e)}")
            raise

    async def create(self, data: Dict[str, Any]) -> Dict[Any, Any]:
        """Create new entity

        Args:
            data: Entity data as dictionary

        Returns:
            Created entity dict

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info(f"Creating {self.model_name}")
            result = await self._model.create(data=data)
            logger.info(f"Created {self.model_name} with id: {result.id}")
            return result
        except Exception as e:
            logger.error(f"Error creating {self.model_name}: {str(e)}")
            raise

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Update entity by ID

        Args:
            id: Entity ID
            data: Updated data as dictionary

        Returns:
            Updated entity dict if found, None otherwise

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info(f"Updating {self.model_name} with id: {id}")
            result = await self._model.update(where={"id": id}, data=data)
            logger.info(f"Updated {self.model_name} with id: {id}")
            return result
        except Exception as e:
            logger.error(f"Error updating {self.model_name} with id {id}: {str(e)}")
            raise

    async def delete(self, id: str) -> bool:
        """Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted successfully

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info(f"Deleting {self.model_name} with id: {id}")
            await self._model.delete(where={"id": id})
            logger.info(f"Deleted {self.model_name} with id: {id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model_name} with id {id}: {str(e)}")
            raise

    async def count(self, where: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria

        Args:
            where: Optional filter criteria

        Returns:
            Number of matching entities

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Counting {self.model_name}")
            count = await self._model.count(where=where or {})
            return count
        except Exception as e:
            logger.error(f"Error counting {self.model_name}: {str(e)}")
            raise

    async def exists(self, id: str) -> bool:
        """Check if entity exists by ID

        Args:
            id: Entity ID

        Returns:
            True if entity exists, False otherwise
        """
        try:
            result = await self.find_by_id(id)
            return result is not None
        except Exception:
            return False
