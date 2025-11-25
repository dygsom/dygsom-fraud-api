"""
Dependency injection for FastAPI.
Provides instances of services and repositories with proper initialization.
"""

from prisma import Prisma
from src.services.fraud_service import FraudService
from src.repositories.transaction_repository import TransactionRepository
from src.ml.ml_service import MLService
import logging

logger = logging.getLogger(__name__)

# Global Prisma client instance
# In production, this should be managed with proper lifecycle
_prisma_client = None


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


async def get_fraud_service() -> FraudService:
    """Get FraudService instance with dependencies

    Dependency injection for FraudService.
    Creates all required dependencies (Prisma, Repository, MLService).

    Returns:
        FraudService instance ready to use

    Raises:
        Exception: If service initialization fails
    """
    try:
        logger.debug("Initializing FraudService dependencies")

        # Get Prisma client
        prisma_client = await get_prisma()

        # Initialize repository
        transaction_repository = TransactionRepository(prisma_client)

        # Initialize FraudService
        fraud_service = FraudService(transaction_repository)

        logger.debug("FraudService dependencies initialized successfully")

        return fraud_service

    except Exception as e:
        logger.error(
            "Failed to initialize FraudService",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise
