"""
Fraud Service - Business logic for fraud detection.
Implements fraud scoring with ML model and velocity checks.
Day 6: Integrated with XGBoost via FeatureEngineer and MLService.
Day 7: Added Prometheus metrics tracking.
"""

from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.cache_repository import CacheRepository
from src.schemas.transaction_schemas import CreateTransactionDto, TransactionResponseDto
from src.ml.features.feature_engineering import FeatureEngineer
from src.ml.ml_service import MLService
from src.core.metrics import (
    track_prediction,
    track_transaction,
    track_feature_extraction,
    track_ml_error,
)

logger = logging.getLogger(__name__)


# Import centralized configuration
from src.core.config import settings

# Risk levels
RISK_LEVEL_LOW = "LOW"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_CRITICAL = "CRITICAL"

# Recommendations
RECOMMENDATION_APPROVE = "APPROVE"
RECOMMENDATION_REVIEW = "REVIEW"
RECOMMENDATION_DECLINE = "DECLINE"


class FraudService:
    """Service for fraud detection operations
    
    Handles fraud scoring using XGBoost ML model with FeatureEngineer.
    Day 6: Integrated with 70+ features and ModelManager.
    """
    
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        cache_repo: Optional[CacheRepository] = None,
        ml_service: Optional[MLService] = None,
        feature_engineer: Optional[FeatureEngineer] = None
    ):
        """Initialize FraudService
        
        Args:
            transaction_repo: Transaction repository instance
            cache_repo: Cache repository instance (optional, for performance optimization)
            ml_service: ML service instance (optional, uses singleton if provided for performance)
            feature_engineer: Feature engineer instance (optional, uses singleton if provided for performance)
        """
        self.transaction_repo = transaction_repo
        self.cache_repo = cache_repo
        
        # Use provided instances or create new ones (singleton pattern for performance)
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.ml_service = ml_service or MLService()
        
        logger.info(
            "FraudService initialized with ML integration",
            extra={
                "cache_enabled": cache_repo is not None,
                "feature_count": self.feature_engineer.get_feature_count(),
                "ml_service_version": self.ml_service.model_version
            }
        )
    
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
            ml_start_time = time.time()
            fraud_score = await self._calculate_fraud_score(
                transaction_data,
                velocity_features
            )
            ml_duration = time.time() - ml_start_time
            
            logger.debug(
                "Fraud score calculated",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "fraud_score": fraud_score,
                    "ml_duration_ms": ml_duration * 1000
                }
            )
            
            # 3. Determine risk level based on fraud score
            risk_level = self._calculate_risk_level(fraud_score)
            
            # 4. Generate recommendation
            recommendation = self._generate_recommendation(fraud_score, risk_level)
            
            # Track ML prediction metrics (Day 7)
            model_version = getattr(self.ml_service, 'model_version', 'unknown') or "unknown"
            track_prediction(
                model_version=model_version,
                fraud_score=fraud_score,
                risk_level=risk_level,
                recommendation=recommendation,
                duration=ml_duration,
            )
            
            # Track transaction business metrics (Day 7)
            track_transaction(
                amount=transaction_data.amount,
                currency=transaction_data.currency,
                risk_level=risk_level,
            )
            
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
            
            # Try cache first if cache_repo exists
            if self.cache_repo:
                cached_features = await self.cache_repo.get_velocity_features(customer_email)
                if cached_features:
                    logger.debug(
                        "Using cached velocity features",
                        extra={
                            "transaction_id": transaction_data.transaction_id,
                            "customer_email": customer_email
                        }
                    )
                    return cached_features
            
            # Cache miss or no cache - calculate from DB
            logger.debug(
                "Calculating velocity features from DB",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "customer_email": customer_email
                }
            )
            
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
            
            # Cache for next request if cache_repo exists
            if self.cache_repo:
                await self.cache_repo.set_velocity_features(
                    customer_email,
                    velocity_features
                )
                logger.debug(
                    "Velocity features cached",
                    extra={
                        "transaction_id": transaction_data.transaction_id,
                        "customer_email": customer_email
                    }
                )
            
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
        """Calculate fraud score using ML model
        
        Day 6: Uses FeatureEngineer to extract 70+ features and MLService for prediction.
        Day 7: Added metrics tracking for ML predictions.
        
        Args:
            transaction_data: Transaction data
            velocity_features: Extracted velocity features
            
        Returns:
            Fraud score between 0.0 and 1.0
        """
        ml_start_time = time.time()
        
        try:
            # Track feature extraction time
            feature_start_time = time.time()
            
            # Convert DTO to dictionary for feature extraction
            transaction_dict = {
                'transaction_id': transaction_data.transaction_id,
                'amount': transaction_data.amount,
                'currency': transaction_data.currency,
                'timestamp': transaction_data.timestamp.isoformat() if transaction_data.timestamp else datetime.utcnow().isoformat(),
                'customer': {
                    'email': transaction_data.customer.email,
                    'customer_id': transaction_data.customer.customer_id
                },
                'payment_method': {
                    'type': transaction_data.payment_method.type
                },
                'merchant': {
                    'category': transaction_data.merchant.category if transaction_data.merchant else 'unknown'
                },
                'ip_address': transaction_data.customer.ip_address,
                'device_id': getattr(transaction_data.customer, 'device_id', None)
            }
            
            # Extract all features using FeatureEngineer
            all_features = self.feature_engineer.extract_all_features(
                transaction_dict,
                velocity_features
            )
            
            feature_duration = time.time() - feature_start_time
            track_feature_extraction("all_features", feature_duration)
            
            logger.debug(
                "Features extracted for ML prediction",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "feature_count": len(all_features),
                    "feature_extraction_ms": feature_duration * 1000
                }
            )
            
            # Use MLService for prediction
            ml_result = self.ml_service.predict(all_features)
            
            # Extract fraud_probability (0-1)
            fraud_score = ml_result.get('fraud_probability', 0.0)
            model_version = self.ml_service.model_version or "unknown"
            
            logger.info(
                "ML prediction completed",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "fraud_score": fraud_score,
                    "fraud_score_100": ml_result.get('fraud_score'),
                    "model_used": ml_result.get('model_used'),
                    "model_version": model_version,
                    "confidence": ml_result.get('confidence')
                }
            )
            
            return fraud_score
            
        except Exception as e:
            ml_duration = time.time() - ml_start_time
            model_version = getattr(self.ml_service, 'model_version', 'unknown') or "unknown"
            
            # Track ML error
            track_ml_error(model_version, type(e).__name__)
            
            logger.error(
                "Error in ML fraud scoring, falling back to 0.0",
                extra={
                    "transaction_id": transaction_data.transaction_id,
                    "error": str(e),
                    "model_version": model_version
                },
                exc_info=True
            )
            # Return low score on error
            return 0.0
    
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
        if fraud_score < settings.FRAUD_SCORE_LOW_THRESHOLD:
            return RISK_LEVEL_LOW
        elif fraud_score < settings.FRAUD_SCORE_MEDIUM_THRESHOLD:
            return RISK_LEVEL_MEDIUM
        elif fraud_score < settings.FRAUD_SCORE_HIGH_THRESHOLD:
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