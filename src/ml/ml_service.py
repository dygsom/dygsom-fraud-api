"""
Machine Learning Service for fraud prediction.

Day 6 implementation with XGBoost model integration.
Uses ModelManager for predictions with fallback to rule-based scoring.
"""

from typing import Dict, Any
import logging
from .model_manager import ModelManager

logger = logging.getLogger(__name__)

# Model configuration constants
MODEL_VERSION_XGBOOST = "v2.0.0-xgboost"
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.5
HIGH_RISK_THRESHOLD = 0.8


class MLService:
    """Machine Learning service for fraud prediction

    Day 6 Implementation: Uses trained XGBoost model via ModelManager.
    Falls back to rule-based scoring if model is unavailable.

    Attributes:
        model_version: Version identifier for the model
        model_manager: ModelManager instance for predictions
    """

    def __init__(self):
        """Initialize MLService with XGBoost model

        Loads trained model via ModelManager. Falls back gracefully if unavailable.
        """
        self.model_version = MODEL_VERSION_XGBOOST
        self.model_manager = ModelManager()
        
        # Try to load model on initialization
        model_loaded = self.model_manager.load_model()
        
        if model_loaded:
            logger.info(f"MLService initialized with XGBoost model version: {self.model_version}")
        else:
            logger.warning("MLService initialized without model - will use fallback predictions")
            self.model_version = "v1.0.0-fallback"

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud probability for transaction

        Day 6 Implementation: Uses trained XGBoost model via ModelManager.

        Args:
            features: Dict containing extracted features (70+)
                Features should be extracted by FeatureEngineer before calling this.

        Returns:
            Dict with prediction results:
                - fraud_score: Float between 0 and 100
                - fraud_probability: Float between 0 and 1
                - risk_level: LOW, MEDIUM, HIGH, or CRITICAL
                - recommendation: APPROVE, REVIEW, or DECLINE
                - model_version: Version of the model used
                - model_used: Whether ML model was used (vs fallback)
                - confidence: Prediction confidence level

        Raises:
            ValueError: If required features are missing
            Exception: If prediction fails
        """
        try:
            logger.debug(
                "Running ML prediction",
                extra={"feature_count": len(features), "model_version": self.model_version},
            )

            # Use ModelManager for prediction
            prediction_result = self.model_manager.predict(features)
            
            # Extract results
            fraud_score = prediction_result['fraud_score']  # Already 0-100
            fraud_probability = prediction_result['fraud_probability']  # 0-1
            
            # Determine risk level and recommendation
            risk_level = self._get_risk_level(fraud_probability)
            recommendation = self._get_recommendation(risk_level)

            result = {
                "fraud_score": fraud_score,
                "fraud_probability": fraud_probability,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "model_version": self.model_version,
                "model_used": prediction_result.get('model_used', False),
                "confidence": prediction_result.get('confidence', 'UNKNOWN')
            }

            logger.info(
                "ML prediction completed",
                extra={
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "recommendation": recommendation,
                    "model_used": result['model_used'],
                    "confidence": result['confidence']
                },
            )

            return result

        except ValueError as e:
            logger.error(f"Validation error in ML prediction: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                "Error in ML prediction",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    def _get_risk_level(self, fraud_probability: float) -> str:
        """Determine risk level from fraud probability

        Args:
            fraud_probability: Fraud probability (0-1)

        Returns:
            Risk level: LOW, MEDIUM, HIGH, or CRITICAL
        """
        if fraud_probability < LOW_RISK_THRESHOLD:
            return "LOW"
        elif fraud_probability < MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        elif fraud_probability < HIGH_RISK_THRESHOLD:
            return "HIGH"
        else:
            return "CRITICAL"

    def _get_recommendation(self, risk_level: str) -> str:
        """Get business recommendation based on risk level

        Args:
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            Recommendation: APPROVE, REVIEW, or DECLINE
        """
        if risk_level == "LOW":
            return "APPROVE"
        elif risk_level == "MEDIUM":
            return "REVIEW"
        else:  # HIGH or CRITICAL
            return "DECLINE"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model
        
        Returns:
            Dictionary with model information
        """
        return self.model_manager.get_model_info()
