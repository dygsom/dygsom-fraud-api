"""
Dashboard endpoints for analytics and API key management.
Provides transaction history, analytics, and API key CRUD operations.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
import logging

from src.dependencies import get_prisma, get_current_user
from prisma import Prisma

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Response Models
class TransactionResponse(BaseModel):
    """Transaction response model"""
    id: str
    transaction_id: str
    amount: float
    currency: str
    fraud_score: Optional[float]
    risk_level: Optional[str]
    decision: Optional[str]
    customer_email: Optional[str]
    customer_ip: Optional[str]
    timestamp: datetime


class TransactionsListResponse(BaseModel):
    """Paginated transactions response"""
    transactions: List[TransactionResponse]
    total: int
    limit: int
    offset: int


class RiskDistribution(BaseModel):
    """Risk level distribution model"""
    low: int
    medium: int
    high: int
    critical: int


class TransactionsByDay(BaseModel):
    """Daily transaction stats model"""
    date: str
    total: int
    fraud_count: int
    total_amount: float


class FraudByPaymentMethod(BaseModel):
    """Fraud stats by payment method"""
    payment_method: str
    total_transactions: int
    fraud_count: int
    fraud_rate: float


class AnalyticsSummary(BaseModel):
    """Analytics summary model - Complete response for Dashboard"""
    total_transactions: int
    fraud_detected: int
    fraud_percentage: float  # Decimal value 0-1 (e.g., 0.08 = 8%)
    total_amount: float
    avg_risk_score: float    # ← Renamed from avg_fraud_score to match Dashboard
    risk_distribution: RiskDistribution
    transactions_by_day: List[TransactionsByDay] 
    fraud_by_payment_method: List[FraudByPaymentMethod]


class ApiKeyResponse(BaseModel):
    """API key metadata response (without actual key)"""
    id: str
    name: str
    description: Optional[str]
    rate_limit: int
    is_active: bool
    request_count: int
    last_used_at: Optional[datetime]
    created_at: datetime


class CreateApiKeyRequest(BaseModel):
    """Create API key request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate_limit: int = Field(default=1000, ge=100, le=10000)


class CreateApiKeyResponse(BaseModel):
    """Create API key response (includes plain key ONCE)"""
    api_key: str
    id: str
    name: str
    rate_limit: int
    created_at: datetime
    warning: str = "Save this key now. You won't be able to see it again."


@router.get("/transactions", response_model=TransactionsListResponse)
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma),
    limit: int = Query(100, le=1000, ge=1, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter")
):
    """
    Get transactions for current organization.

    Filters available:
    - risk_level: LOW, MEDIUM, HIGH, CRITICAL
    - date_from: Start date (ISO format)
    - date_to: End date (ISO format)
    - limit: Max results (default 100, max 1000)
    - offset: Pagination offset

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client
        limit: Maximum number of results
        offset: Pagination offset
        risk_level: Risk level filter
        date_from: Start date filter
        date_to: End date filter

    Returns:
        Paginated list of transactions

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    organization_id = current_user.get("organization_id")

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization"
        )

    try:
        # Build filters
        where = {}

        if risk_level:
            if risk_level not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid risk_level. Must be: LOW, MEDIUM, HIGH, or CRITICAL"
                )
            where["risk_level"] = risk_level

        # Date range filter
        if date_from or date_to:
            where["timestamp"] = {}
            if date_from:
                where["timestamp"]["gte"] = date_from
            if date_to:
                where["timestamp"]["lte"] = date_to

        # Query transactions
        # Note: We'll need to add organization_id to Transaction model or filter by API key
        transactions = await prisma.transaction.find_many(
            where=where,
            order={"timestamp": "desc"},
            take=limit,
            skip=offset
        )

        # Count total
        total = await prisma.transaction.count(where=where)

        # Convert to response format
        transaction_responses = [
            TransactionResponse(
                id=tx.id,
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                fraud_score=float(tx.fraud_score) if tx.fraud_score else None,
                risk_level=tx.risk_level,
                decision=tx.decision,
                customer_email=tx.customer_email,
                customer_ip=tx.customer_ip,
                timestamp=tx.timestamp
            )
            for tx in transactions
        ]

        return TransactionsListResponse(
            transactions=transaction_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get transactions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze (1-90)")
):
    """
    Get analytics summary for last N days.

    Returns:
    - Total transactions
    - Fraud detected (HIGH or CRITICAL risk)
    - Fraud rate percentage
    - Total amount analyzed
    - Average fraud score

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client
        days: Number of days to analyze

    Returns:
        Analytics summary

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        date_from = datetime.utcnow() - timedelta(days=days)

        # Get transactions in time range with organization filtering
        transactions = await prisma.transaction.find_many(
            where={
                "organization_id": current_user.get("organization_id"),  # CRITICAL: Organization isolation
                "timestamp": {"gte": date_from}
            }
        )

        total_transactions = len(transactions)

        if total_transactions == 0:
            return AnalyticsSummary(
                total_transactions=0,
                fraud_detected=0,
                fraud_percentage=0.0,
                total_amount=0.0,
                avg_risk_score=0.0,
                risk_distribution=RiskDistribution(low=0, medium=0, high=0, critical=0),
                transactions_by_day=[],
                fraud_by_payment_method=[]
            )

        # Count fraud (HIGH or CRITICAL)
        fraud_detected = sum(
            1 for tx in transactions
            if tx.risk_level in ["HIGH", "CRITICAL"]
        )

        # Calculate fraud rate
        fraud_rate = (fraud_detected / total_transactions * 100) if total_transactions > 0 else 0

        # Sum amounts
        total_amount = sum(float(tx.amount) for tx in transactions)

        # Average fraud score (renamed to avg_risk_score for Dashboard compatibility)
        fraud_scores = [float(tx.fraud_score) for tx in transactions if tx.fraud_score is not None]
        avg_risk_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

        # Calculate risk distribution
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for tx in transactions:
            risk_level = tx.risk_level or "LOW"
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

        risk_distribution = RiskDistribution(
            low=risk_counts["LOW"],
            medium=risk_counts["MEDIUM"], 
            high=risk_counts["HIGH"],
            critical=risk_counts["CRITICAL"]
        )

        # Calculate daily transaction stats
        daily_stats = {}
        for tx in transactions:
            date_key = tx.timestamp.date().isoformat()
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "total": 0,
                    "fraud_count": 0,
                    "total_amount": 0.0
                }
            
            daily_stats[date_key]["total"] += 1
            daily_stats[date_key]["total_amount"] += float(tx.amount)
            
            if tx.risk_level in ["HIGH", "CRITICAL"]:
                daily_stats[date_key]["fraud_count"] += 1

        transactions_by_day = [
            TransactionsByDay(
                date=stats["date"],
                total=stats["total"],
                fraud_count=stats["fraud_count"],
                total_amount=round(stats["total_amount"], 2)
            )
            for stats in sorted(daily_stats.values(), key=lambda x: x["date"])
        ]

        # Calculate fraud by payment method (mock for now since we don't have this field)
        # TODO: Add payment_method field to Transaction model
        fraud_by_payment_method = []
        
        # Credit Card method stats
        cc_transactions = max(1, int(total_transactions * 0.6))
        cc_frauds = max(0, int(fraud_detected * 0.4))
        cc_fraud_rate = (cc_frauds / cc_transactions) if cc_transactions > 0 else 0
        
        # Debit Card method stats  
        dc_transactions = max(1, int(total_transactions * 0.3))
        dc_frauds = max(0, int(fraud_detected * 0.35))
        dc_fraud_rate = (dc_frauds / dc_transactions) if dc_transactions > 0 else 0
        
        # Bank Transfer method stats
        bt_transactions = max(1, int(total_transactions * 0.1))
        bt_frauds = max(0, int(fraud_detected * 0.25))
        bt_fraud_rate = (bt_frauds / bt_transactions) if bt_transactions > 0 else 0
        
        fraud_by_payment_method = [
            FraudByPaymentMethod(
                payment_method="credit_card",
                total_transactions=cc_transactions,
                fraud_count=cc_frauds,
                fraud_rate=round(cc_fraud_rate, 4)  # ← Decimal (0-1) para consistencia
            ),
            FraudByPaymentMethod(
                payment_method="debit_card", 
                total_transactions=dc_transactions,
                fraud_count=dc_frauds,
                fraud_rate=round(dc_fraud_rate, 4)  # ← Decimal (0-1) para consistencia
            ),
            FraudByPaymentMethod(
                payment_method="bank_transfer",
                total_transactions=bt_transactions,
                fraud_count=bt_frauds,
                fraud_rate=round(bt_fraud_rate, 4)  # ← Decimal (0-1) para consistencia
            )
        ]

        return AnalyticsSummary(
            total_transactions=total_transactions,
            fraud_detected=fraud_detected,
            fraud_percentage=round(fraud_rate / 100, 4),  # ← Enviar como decimal (0-1) para formatPercentage
            total_amount=round(total_amount, 2),
            avg_risk_score=round(avg_risk_score, 3),  # ← Renamed from avg_fraud_score
            risk_distribution=risk_distribution,
            transactions_by_day=transactions_by_day,
            fraud_by_payment_method=fraud_by_payment_method
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics summary error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.get("/analytics/fraud-rate-over-time")
async def get_fraud_rate_over_time(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get fraud rate over time (daily aggregation).

    Returns array of:
    {
        "date": "2025-01-25",
        "total": 1000,
        "fraud_count": 50,
        "fraud_rate": 5.0
    }

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client
        days: Number of days to analyze

    Returns:
        List of daily fraud rate statistics

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        date_from = datetime.utcnow() - timedelta(days=days)

        # Get transactions with organization filtering
        transactions = await prisma.transaction.find_many(
            where={
                "organization_id": current_user.get("organization_id"),  # CRITICAL: Organization isolation
                "timestamp": {"gte": date_from}
            },
            order={"timestamp": "asc"}
        )

        # Group by date
        daily_stats = {}
        for tx in transactions:
            date_key = tx.timestamp.date().isoformat()

            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "total": 0,
                    "fraud_count": 0
                }

            daily_stats[date_key]["total"] += 1

            if tx.risk_level in ["HIGH", "CRITICAL"]:
                daily_stats[date_key]["fraud_count"] += 1

        # Calculate fraud rate for each day
        results = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            fraud_rate = (stats["fraud_count"] / stats["total"] * 100) if stats["total"] > 0 else 0

            results.append({
                "date": stats["date"],
                "total": stats["total"],
                "fraud_count": stats["fraud_count"],
                "fraud_rate": round(fraud_rate, 2)
            })

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get fraud rate over time error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fraud rate over time"
        )


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get risk level distribution.

    Returns:
    {
        "LOW": 850,
        "MEDIUM": 120,
        "HIGH": 25,
        "CRITICAL": 5
    }

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client
        days: Number of days to analyze

    Returns:
        Risk level distribution counts

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        date_from = datetime.utcnow() - timedelta(days=days)

        # Get transactions with organization filtering
        transactions = await prisma.transaction.find_many(
            where={
                "organization_id": current_user.get("organization_id"),  # CRITICAL: Organization isolation
                "timestamp": {"gte": date_from}
            }
        )

        # Count by risk level
        distribution = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }

        for tx in transactions:
            if tx.risk_level and tx.risk_level in distribution:
                distribution[tx.risk_level] += 1

        return distribution

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get risk distribution error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk distribution"
        )


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma)
):
    """
    Get all API keys for current organization.

    Note: Does not return actual keys, only metadata.

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client

    Returns:
        List of API keys (metadata only)

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    organization_id = current_user.get("organization_id")

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization"
        )

    try:
        api_keys = await prisma.apikey.find_many(
            where={"organization_id": organization_id},
            order={"created_at": "desc"}
        )

        return [
            ApiKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                rate_limit=key.rate_limit,
                is_active=key.is_active,
                request_count=key.request_count,
                last_used_at=key.last_used_at,
                created_at=key.created_at
            )
            for key in api_keys
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get API keys error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma)
):
    """
    Create new API key for current organization.

    Returns the plain key ONCE. User must save it.

    Args:
        request: Create API key request
        current_user: Current user from JWT token
        prisma: Prisma database client

    Returns:
        Created API key (with plain key - shown only once)

    Raises:
        HTTPException 401: If user not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    organization_id = current_user.get("organization_id")
    user_id = current_user.get("user_id")

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization"
        )

    try:
        # Import functions from auth.py
        from src.api.v1.endpoints.auth import generate_api_key, hash_api_key

        # Generate key
        api_key_plain = generate_api_key()
        api_key_hash = hash_api_key(api_key_plain)

        # Create in database
        api_key = await prisma.apikey.create(
            data={
                "key_hash": api_key_hash,
                "name": request.name,
                "description": request.description,
                "organization_id": organization_id,
                "rate_limit": request.rate_limit,
                "created_by": user_id
            }
        )

        logger.info(f"API key created: {api_key.id} for organization: {organization_id}")

        return CreateApiKeyResponse(
            api_key=api_key_plain,  # ONLY time we return plain key
            id=api_key.id,
            name=api_key.name,
            rate_limit=api_key.rate_limit,
            created_at=api_key.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create API key error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_200_OK)
async def deactivate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma)
):
    """
    Deactivate API key (soft delete).

    Args:
        key_id: API key ID to deactivate
        current_user: Current user from JWT token
        prisma: Prisma database client

    Returns:
        Success message

    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 404: If API key not found
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    organization_id = current_user.get("organization_id")

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with an organization"
        )

    try:
        # Verify key belongs to organization
        api_key = await prisma.apikey.find_first(
            where={
                "id": key_id,
                "organization_id": organization_id
            }
        )

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Deactivate (soft delete)
        await prisma.apikey.update(
            where={"id": key_id},
            data={"is_active": False}
        )

        logger.info(f"API key deactivated: {key_id}")

        return {"message": "API key deactivated successfully", "key_id": key_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate API key error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate API key"
        )
