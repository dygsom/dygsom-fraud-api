"""
Fraud Service - Business logic for fraud detection.
Implements fraud scoring with velocity checks and risk level calculation.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from src.repositories.transaction_repository import TransactionRepository
from src.schemas.transaction_schemas import CreateTransactionDto, TransactionResponseDto

logger = logging.getLogger(__name__)


# Business rules constants
FRAUD_SCORE_LOW_THRESHOLD = 0.3
FRAUD_SCORE_MEDIUM_THRESHOLD = 0.5
FRAUD_SCORE_HIGH_THRESHOLD = 0.8

# Risk levels
RISK_LEVEL_LOW = "LOW"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_CRITICAL = "CRITICAL"

# Recommendations
RECOMMENDATION_APPROVE = "APPROVE"
RECOMMENDATION_REVIEW = "REVIEW"
RECOMMENDATION_DECLINE = "DECLINE"

# Velocity check limits
MAX_TRANSACTIONS_PER_HOUR = 5
MAX_TRANSACTIONS_PER_DAY = 20
MAX_AMOUNT_PER_DAY = 10000.00


class FraudService:
    """Service for fraud detection operations
    
    Handles fraud scoring, risk level calculation, and transaction recommendations.
    Implements velocity checks and business rules for fraud detection.
    """
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        # ml_service will be added later when ML component is ready
        # cache_service will be added later for performance optimization
    ):
        """Initialize FraudService
        
        Args:
            transaction_repo: Transaction repository instance
        """
        self.transaction_repo = transaction_repo
        logger.info("FraudService initialized")
    
    async def score_transaction(self, transaction_data: CreateTransactionDto) -> Dict[str, Any]:
        """Score transaction for fraud risk
        
        Main method that orchestrates fraud detection process:
        1. Validate transaction
        2. Extract velocity features
        3. Calculate fraud score (placeholder until ML model is integrated)
        4. Determine risk level
        5. Generate recommendation
        6. Save transaction to database
        
        Args:
            transaction_data: Validated transaction DTO
            
        Returns:
            Dict with fraud scoring results
            
        Raises:
            Exception: If transaction processing fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Starting fraud scoring",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "amount": transaction_data.amount,
                    "currency": transaction_data.currency,
                    "customer_email": transaction_data.customer.email
                }
            )
            
            # 1. Extract velocity features
            velocity_features = await self._extract_velocity_features(transaction_data)
            
            logger.debug(
                "Velocity features extracted",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "features": velocity_features
                }
            )
            
            # 2. Calculate fraud score
            # TODO: Replace with actual ML model prediction when ready
            fraud_score = await self._calculate_fraud_score(
                transaction_data,
                velocity_features
            )
            
            logger.debug(
                "Fraud score calculated",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "fraud_score": fraud_score
                }
            )
            
            # 3. Determine risk level based on fraud score
            risk_level = self._calculate_risk_level(fraud_score)
            
            # 4. Generate recommendation
            recommendation = self._generate_recommendation(fraud_score, risk_level)
            
            logger.info(
                "Fraud analysis completed",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "recommendation": recommendation
                }
            )
            
            # 5. Save transaction to database
            transaction_record = await self._save_transaction(
                transaction_data,
                fraud_score,
                risk_level,
                recommendation
            )
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(
                "Transaction saved successfully",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "processing_time_ms": processing_time_ms,
                    "db_id": transaction_record.id if hasattr(transaction_record, 'id') else None
                }
            )
            
            # 6. Build response
            response = {
                "transaction_id": transaction_data.transaction_id,
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "processing_time_ms": processing_time_ms,
                "timestamp": transaction_data.timestamp,
                "details": {
                    "amount": transaction_data.amount,
                    "currency": transaction_data.currency,
                    "customer_email": transaction_data.customer.email,
                    "velocity_checks": velocity_features
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(
                "Error scoring transaction",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
    
    async def _extract_velocity_features(
        self,
        transaction_data: CreateTransactionDto
    ) -> Dict[str, Any]:
        """Extract velocity features for fraud detection
        
        Calculates transaction counts and amounts for customer and IP.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            Dict with velocity features
            
        Raises:
            Exception: If velocity feature extraction fails
        """
        try:
            customer_email = transaction_data.customer.email
            customer_ip = transaction_data.customer.ip_address
            
            # Get customer transaction counts
            customer_tx_1h = await self.transaction_repo.get_customer_transaction_count(
                customer_email,
                hours=1
            )
            
            customer_tx_24h = await self.transaction_repo.get_customer_transaction_count(
                customer_email,
                hours=24
            )
            
            # Get customer transaction amounts
            customer_amount_24h = await self.transaction_repo.get_customer_transaction_amount_sum(
                customer_email,
                hours=24
            )
            
            # Get IP transaction counts
            ip_history_1h = await self.transaction_repo.get_ip_history(
                customer_ip,
                hours=1
            )
            ip_tx_1h = len(ip_history_1h)
            
            ip_history_24h = await self.transaction_repo.get_ip_history(
                customer_ip,
                hours=24
            )
            ip_tx_24h = len(ip_history_24h)
            
            velocity_features = {
                "customer_tx_count_1h": customer_tx_1h,
                "customer_tx_count_24h": customer_tx_24h,
                "customer_amount_24h": float(customer_amount_24h),
                "ip_tx_count_1h": ip_tx_1h,
                "ip_tx_count_24h": ip_tx_24h,
            }
            
            return velocity_features
            
        except Exception as e:
            logger.error(
                "Error extracting velocity features",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "error": str(e)
                }
            )
            raise
    
    async def _calculate_fraud_score(
        self,
        transaction_data: CreateTransactionDto,
        velocity_features: Dict[str, Any]
    ) -> float:
        """Calculate fraud score for transaction
        
        TODO: Replace with actual ML model prediction.
        Currently uses rule-based scoring based on velocity checks.
        
        Args:
            transaction_data: Transaction data
            velocity_features: Extracted velocity features
            
        Returns:
            Fraud score between 0.0 and 1.0
        """
        # Placeholder fraud score calculation (rule-based)
        # This will be replaced with ML model prediction
        
        score = 0.0
        
        # High transaction count in last hour (max 20 points)
        if velocity_features["customer_tx_count_1h"] > MAX_TRANSACTIONS_PER_HOUR:
            score += 0.20
        elif velocity_features["customer_tx_count_1h"] > 3:
            score += 0.10
        
        # High transaction count in last 24h (max 20 points)
        if velocity_features["customer_tx_count_24h"] > MAX_TRANSACTIONS_PER_DAY:
            score += 0.20
        elif velocity_features["customer_tx_count_24h"] > 10:
            score += 0.10
        
        # High amount in last 24h (max 20 points)
        if velocity_features["customer_amount_24h"] > MAX_AMOUNT_PER_DAY:
            score += 0.20
        elif velocity_features["customer_amount_24h"] > 5000:
            score += 0.10
        
        # High IP transaction count (max 20 points)
        if velocity_features["ip_tx_count_1h"] > 10:
            score += 0.20
        elif velocity_features["ip_tx_count_1h"] > 5:
            score += 0.10
        
        # Large transaction amount (max 20 points)
        if transaction_data.amount > 5000:
            score += 0.20
        elif transaction_data.amount > 2000:
            score += 0.10
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Round to 4 decimal places
        return round(score, 4)
    
    def _calculate_risk_level(self, fraud_score: float) -> str:
        """Calculate risk level based on fraud score
        
        Business rules:
        - LOW: score < 0.3
        - MEDIUM: 0.3 <= score < 0.5
        - HIGH: 0.5 <= score < 0.8
        - CRITICAL: score >= 0.8
        
        Args:
            fraud_score: Fraud probability score (0-1)
            
        Returns:
            Risk level string
        """
        if fraud_score < FRAUD_SCORE_LOW_THRESHOLD:
            return RISK_LEVEL_LOW
        elif fraud_score < FRAUD_SCORE_MEDIUM_THRESHOLD:
            return RISK_LEVEL_MEDIUM
        elif fraud_score < FRAUD_SCORE_HIGH_THRESHOLD:
            return RISK_LEVEL_HIGH
        else:
            return RISK_LEVEL_CRITICAL
    
    def _generate_recommendation(self, fraud_score: float, risk_level: str) -> str:
        """Generate recommendation based on fraud score and risk level
        
        Business rules:
        - APPROVE: LOW risk
        - REVIEW: MEDIUM risk or HIGH risk with score < 0.7
        - DECLINE: HIGH risk with score >= 0.7 or CRITICAL risk
        
        Args:
            fraud_score: Fraud probability score (0-1)
            risk_level: Risk level string
            
        Returns:
            Recommendation string
        """
        if risk_level == RISK_LEVEL_LOW:
            return RECOMMENDATION_APPROVE
        elif risk_level == RISK_LEVEL_MEDIUM:
            return RECOMMENDATION_REVIEW
        elif risk_level == RISK_LEVEL_HIGH:
            # HIGH risk with lower score -> review, higher score -> decline
            if fraud_score < 0.7:
                return RECOMMENDATION_REVIEW
            else:
                return RECOMMENDATION_DECLINE
        else:  # CRITICAL
            return RECOMMENDATION_DECLINE
    
    async def _save_transaction(
        self,
        transaction_data: CreateTransactionDto,
        fraud_score: float,
        risk_level: str,
        recommendation: str
    ) -> Dict[str, Any]:
        """Save transaction to database with fraud scoring results
        
        Args:
            transaction_data: Transaction data
            fraud_score: Calculated fraud score
            risk_level: Risk level
            recommendation: Recommendation
            
        Returns:
            Saved transaction record
            
        Raises:
            Exception: If database save fails
        """
        try:
            transaction_dict = {
                "transaction_id": transaction_data.transaction_id,
                "amount": transaction_data.amount,
                "currency": transaction_data.currency,
                "timestamp": transaction_data.timestamp,
                
                # Customer data
                "customer_id": transaction_data.customer.id,
                "customer_email": transaction_data.customer.email,
                "customer_phone": transaction_data.customer.phone,
                "customer_ip": transaction_data.customer.ip_address,
                
                # Payment method
                "card_bin": transaction_data.payment_method.bin,
                "card_last4": transaction_data.payment_method.last4,
                "card_brand": transaction_data.payment_method.brand,
                
                # Fraud detection results
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "decision": recommendation,
            }
            
            saved_transaction = await self.transaction_repo.create(transaction_dict)
            
            return saved_transaction
            
        except Exception as e:
            logger.error(
                "Error saving transaction to database",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "error": str(e)
                }
            )
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by transaction_id
        
        Args:
            transaction_id: Business transaction ID
            
        Returns:
            Transaction dict if found, None otherwise
        """
        try:
            logger.debug(f"Getting transaction: {transaction_id}")
            transaction = await self.transaction_repo.find_by_transaction_id(transaction_id)
            return transaction
        except Exception as e:
            logger.error(
                "Error getting transaction",
                extra={
                    "transaction_id": transaction_id,
                    "error": str(e)
                }
            )
            raise
    
    async def get_risk_statistics(self) -> Dict[str, int]:
        """Get transaction statistics grouped by risk level
        
        Returns:
            Dict with risk level counts
        """
        try:
            logger.debug("Getting risk statistics")
            statistics = await self.transaction_repo.get_statistics_by_risk_level()
            return statistics
        except Exception as e:
            logger.error("Error getting risk statistics", extra={"error": str(e)})
            raise