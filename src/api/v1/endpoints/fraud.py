"""
Fraud detection endpoint.
Implements POST /score for transaction fraud scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import time
from datetime import datetime
import logging

from src.schemas.transaction_schemas import CreateTransactionDto
from src.services.fraud_service import FraudService
from src.dependencies import get_fraud_service

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.post(
    "/score",
    status_code=status.HTTP_200_OK,
    summary="Score transaction for fraud",
    description="""
    Score a transaction for fraud risk using machine learning and velocity checks.
    
    **Returns:**
    - fraud_score (0-1): Probability of fraud
    - risk_level: LOW, MEDIUM, HIGH, or CRITICAL
    - recommendation: APPROVE, REVIEW, or DECLINE
    - processing_time_ms: API processing time
    
    **Performance:**
    - Target latency: <100ms (p95)
    - Current Day 3: <200ms (will optimize in Day 4)
    
    **Risk Levels:**
    - LOW: fraud_score < 0.3 → Safe to approve
    - MEDIUM: 0.3 <= fraud_score < 0.5 → Review recommended
    - HIGH: 0.5 <= fraud_score < 0.8 → High risk
    - CRITICAL: fraud_score >= 0.8 → Very high risk
    
    **Business Rules:**
    - Velocity checks on customer email and IP
    - Transaction amount analysis
    - Pattern detection based on historical data
    """,
    responses={
        200: {
            "description": "Transaction scored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "transaction_id": "txn_abc123",
                        "fraud_score": 0.15,
                        "risk_level": "LOW",
                        "recommendation": "APPROVE",
                        "processing_time_ms": 87,
                        "timestamp": "2024-11-27T10:30:00Z",
                        "details": {
                            "amount": 150.50,
                            "currency": "PEN",
                            "customer_email": "customer@example.com",
                            "model_version": "v1.0.0-baseline",
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid transaction data"},
        500: {"description": "Internal server error"},
    },
)
async def score_transaction(
    transaction_data: CreateTransactionDto,
    fraud_service: Annotated[FraudService, Depends(get_fraud_service)],
):
    """Score transaction for fraud risk

    Validates transaction data, calculates fraud score using ML and velocity checks,
    determines risk level and recommendation, then saves to database.

    Args:
        transaction_data: Validated transaction data from request body
        fraud_service: Injected FraudService instance

    Returns:
        Dict with fraud scoring results and processing metrics

    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If internal processing fails
    """
    start_time = time.time()

    try:
        logger.info(
            "Incoming fraud score request",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "amount": float(transaction_data.amount),
                "currency": transaction_data.currency,
                "customer_email": transaction_data.customer.email,
            },
        )

        # Call fraud service to score transaction
        result = await fraud_service.score_transaction(transaction_data)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time_ms

        logger.info(
            "Transaction scored successfully",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "fraud_score": result["fraud_score"],
                "risk_level": result["risk_level"],
                "recommendation": result["recommendation"],
                "processing_time_ms": processing_time_ms,
            },
        )

        return result

    except ValueError as e:
        # Validation errors (should be caught by Pydantic, but just in case)
        logger.error(
            "Validation error in fraud scoring",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}",
        )

    except Exception as e:
        # Unexpected errors
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "Error processing fraud score request",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": processing_time_ms,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing transaction",
        )
