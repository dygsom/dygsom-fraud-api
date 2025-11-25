"""
Database connection manager with pooling and graceful shutdown.
Handles Prisma connection lifecycle with retry logic.
"""

from prisma import Prisma
from contextlib import asynccontextmanager
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages Prisma database connections with pooling and lifecycle management.

    Features:
    - Connection retry logic with exponential backoff
    - Graceful shutdown
    - Connection health monitoring
    - Singleton pattern for global access
    """

    def __init__(self):
        """Initialize database manager"""
        self._client: Optional[Prisma] = None
        self._connected = False
        self._max_retries = 3
        self._retry_delay = 2  # seconds

    async def connect(self) -> None:
        """
        Connect to database with retry logic.

        Attempts connection with exponential backoff on failure.

        Raises:
            Exception: If all retry attempts fail
        """
        if self._connected:
            logger.info("Database already connected")
            return

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    f"Connecting to database (attempt {attempt}/{self._max_retries})"
                )

                self._client = Prisma()
                await self._client.connect()
                self._connected = True

                logger.info("Database connected successfully")
                return

            except Exception as e:
                logger.error(
                    f"Database connection attempt {attempt} failed: {str(e)}",
                    exc_info=True
                )

                if attempt < self._max_retries:
                    # Exponential backoff
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.critical("All database connection attempts failed")
                    raise

    async def disconnect(self) -> None:
        """
        Disconnect from database gracefully.

        Closes all connections and cleans up resources.
        """
        if self._client and self._connected:
            try:
                logger.info("Disconnecting from database...")
                await self._client.disconnect()
                self._connected = False
                logger.info("Database disconnected successfully")
            except Exception as e:
                logger.error(
                    f"Error disconnecting from database: {str(e)}",
                    exc_info=True
                )
        else:
            logger.debug("Database already disconnected or never connected")

    def get_client(self) -> Prisma:
        """
        Get Prisma client instance.

        Returns:
            Prisma client instance

        Raises:
            RuntimeError: If database is not connected
        """
        if not self._connected or not self._client:
            raise RuntimeError(
                "Database not connected. Call connect() first or use lifespan manager."
            )
        return self._client

    @property
    def is_connected(self) -> bool:
        """
        Check if database is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    async def health_check(self) -> bool:
        """
        Perform database health check.

        Executes simple query to verify connection is alive.

        Returns:
            True if healthy, False otherwise
        """
        if not self._connected or not self._client:
            logger.warning("Health check failed: Database not connected")
            return False

        try:
            # Simple query to verify connection
            await self._client.execute_raw("SELECT 1")
            logger.debug("Database health check passed")
            return True
        except Exception as e:
            logger.error(
                f"Database health check failed: {str(e)}",
                exc_info=True
            )
            return False


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def lifespan_handler():
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
    - Startup: Connect to database
    - Shutdown: Gracefully disconnect from database

    Usage:
        app = FastAPI(lifespan=lifespan_handler)
    """
    # Startup
    logger.info("Application starting up...")
    try:
        await db_manager.connect()
        logger.info("Startup complete")
    except Exception as e:
        logger.critical(f"Startup failed: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Application shutting down...")
    try:
        await db_manager.disconnect()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)
