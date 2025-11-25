"""
Transaction Repository for database operations.
Implements specific methods for transaction queries and fraud detection.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from prisma import Prisma
from src.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class TransactionRepository(BaseRepository):
    """Repository for Transaction operations

    Extends BaseRepository with transaction-specific queries for fraud detection,
    customer history, and risk analysis.
    """

    def __init__(self, prisma: Prisma):
        """Initialize TransactionRepository

        Args:
            prisma: Prisma client instance
        """
        super().__init__(prisma, model_name="transaction")

    async def find_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[Dict[Any, Any]]:
        """Find transaction by transaction_id (business identifier)

        Args:
            transaction_id: Business transaction ID

        Returns:
            Transaction dict if found, None otherwise

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Finding transaction by transaction_id: {transaction_id}")
            result = await self._model.find_unique(
                where={"transaction_id": transaction_id}
            )
            return result
        except Exception as e:
            logger.error(
                f"Error finding transaction by transaction_id {transaction_id}: {str(e)}"
            )
            raise

    async def get_customer_history(
        self, customer_email: str, hours: int = 24
    ) -> List[Dict[Any, Any]]:
        """Get customer transaction history for last N hours

        Used for velocity checks and pattern detection in fraud scoring.

        Args:
            customer_email: Customer email address
            hours: Number of hours to look back (default: 24)

        Returns:
            List of transaction dicts ordered by timestamp DESC

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(
                f"Getting customer history for {customer_email} (last {hours}h)"
            )

            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            results = await self._model.find_many(
                where={
                    "customer_email": customer_email,
                    "timestamp": {"gte": cutoff_time},
                },
                order={"timestamp": "desc"},
            )

            logger.debug(f"Found {len(results)} transactions for {customer_email}")
            return results
        except Exception as e:
            logger.error(
                f"Error getting customer history for {customer_email}: {str(e)}"
            )
            raise

    async def get_ip_history(
        self, customer_ip: str, hours: int = 24
    ) -> List[Dict[Any, Any]]:
        """Get transaction history for an IP address

        Used for IP-based velocity checks and fraud detection.

        Args:
            customer_ip: Customer IP address
            hours: Number of hours to look back (default: 24)

        Returns:
            List of transaction dicts ordered by timestamp DESC

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Getting IP history for {customer_ip} (last {hours}h)")

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            results = await self._model.find_many(
                where={"customer_ip": customer_ip, "timestamp": {"gte": cutoff_time}},
                order={"timestamp": "desc"},
            )

            logger.debug(f"Found {len(results)} transactions for IP {customer_ip}")
            return results
        except Exception as e:
            logger.error(f"Error getting IP history for {customer_ip}: {str(e)}")
            raise

    async def get_transactions_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[Dict[Any, Any]]:
        """Get transactions within a date range

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of transaction dicts ordered by timestamp DESC

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Getting transactions from {start_date} to {end_date}")

            results = await self._model.find_many(
                where={"timestamp": {"gte": start_date, "lte": end_date}},
                skip=skip,
                take=limit,
                order={"timestamp": "desc"},
            )

            logger.debug(f"Found {len(results)} transactions in date range")
            return results
        except Exception as e:
            logger.error(f"Error getting transactions by date range: {str(e)}")
            raise

    async def count_by_risk_level(self, risk_level: str) -> int:
        """Count transactions by risk level

        Args:
            risk_level: Risk level to count (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            Number of transactions with specified risk level

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Counting transactions with risk_level: {risk_level}")

            count = await self._model.count(where={"risk_level": risk_level})

            logger.debug(f"Found {count} transactions with risk_level {risk_level}")
            return count
        except Exception as e:
            logger.error(
                f"Error counting transactions by risk_level {risk_level}: {str(e)}"
            )
            raise

    async def get_statistics_by_risk_level(self) -> Dict[str, int]:
        """Get transaction count statistics grouped by risk level

        Returns:
            Dict with risk levels as keys and counts as values
            Example: {"LOW": 100, "MEDIUM": 50, "HIGH": 20, "CRITICAL": 5}

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug("Getting transaction statistics by risk level")

            # Get counts for each risk level
            risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            statistics = {}

            for level in risk_levels:
                count = await self.count_by_risk_level(level)
                statistics[level] = count

            # Also count transactions without risk level
            null_count = await self._model.count(where={"risk_level": None})
            statistics["UNSCORED"] = null_count

            logger.debug(f"Risk level statistics: {statistics}")
            return statistics
        except Exception as e:
            logger.error(f"Error getting statistics by risk level: {str(e)}")
            raise

    async def get_high_risk_transactions(
        self, threshold: float = 0.5, skip: int = 0, limit: int = 100
    ) -> List[Dict[Any, Any]]:
        """Get transactions with fraud score above threshold

        Args:
            threshold: Fraud score threshold (default: 0.5)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of high-risk transaction dicts ordered by fraud_score DESC

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Getting high-risk transactions (score >= {threshold})")

            results = await self._model.find_many(
                where={"fraud_score": {"gte": threshold}},
                skip=skip,
                take=limit,
                order={"fraud_score": "desc"},
            )

            logger.debug(f"Found {len(results)} high-risk transactions")
            return results
        except Exception as e:
            logger.error(f"Error getting high-risk transactions: {str(e)}")
            raise

    async def get_customer_transaction_count(
        self, customer_email: str, hours: int = 1
    ) -> int:
        """Count transactions for a customer in last N hours

        Used for velocity checks in fraud detection.

        Args:
            customer_email: Customer email address
            hours: Number of hours to look back (default: 1)

        Returns:
            Number of transactions in time window

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(f"Counting transactions for {customer_email} in last {hours}h")

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            count = await self._model.count(
                where={
                    "customer_email": customer_email,
                    "timestamp": {"gte": cutoff_time},
                }
            )

            logger.debug(
                f"Customer {customer_email} has {count} transactions in last {hours}h"
            )
            return count
        except Exception as e:
            logger.error(f"Error counting customer transactions: {str(e)}")
            raise

    async def get_customer_transaction_amount_sum(
        self, customer_email: str, hours: int = 24
    ) -> float:
        """Sum transaction amounts for a customer in last N hours

        Used for velocity checks and spending pattern analysis.

        Args:
            customer_email: Customer email address
            hours: Number of hours to look back (default: 24)

        Returns:
            Total amount of transactions in time window

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.debug(
                f"Summing transaction amounts for {customer_email} in last {hours}h"
            )

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            transactions = await self._model.find_many(
                where={
                    "customer_email": customer_email,
                    "timestamp": {"gte": cutoff_time},
                }
            )

            # Sum amounts (convert Decimal to float)
            total = sum(float(tx.amount) for tx in transactions if tx.amount)

            logger.debug(
                f"Customer {customer_email} total amount: {total} in last {hours}h"
            )
            return total
        except Exception as e:
            logger.error(f"Error summing customer transaction amounts: {str(e)}")
            raise
