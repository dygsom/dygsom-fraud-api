"""
Machine Learning Service for fraud prediction.

Day 3 implementation uses rule-based scoring (placeholder).
Day 6 will integrate actual XGBoost model trained by Alicia.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Model configuration constants
MODEL_VERSION_BASELINE = "v1.0.0-baseline"
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.5
HIGH_RISK_THRESHOLD = 0.8


class MLService:
    """Machine Learning service for fraud prediction

    Currently implements rule-based scoring as placeholder until
    actual ML model is trained and integrated.

    Attributes:
        model_version: Version identifier for the model
    """

    def __init__(self):
        """Initialize MLService with baseline configuration

        In Day 6, this will load actual trained model from S3 or local storage.
        """
        self.model_version = MODEL_VERSION_BASELINE
        logger.info(f"MLService initialized with version: {self.model_version}")

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud probability for transaction

        Day 3 Implementation: Uses simple rule-based scoring.
        Day 6 Implementation: Will use trained XGBoost model.

        Args:
            features: Dict containing transaction features for prediction
                Expected keys:
                - amount: Transaction amount
                - transactions_last_hour: Count of recent transactions
                - transactions_last_day: Count of daily transactions
                - amount_last_day: Total amount in last 24h
                - customer_email: Customer email
                - customer_ip: Customer IP address

        Returns:
            Dict with prediction results:
                - fraud_score: Float between 0 and 1
                - risk_level: LOW, MEDIUM, HIGH, or CRITICAL
                - recommendation: APPROVE, REVIEW, or DECLINE
                - model_version: Version of the model used

        Raises:
            ValueError: If required features are missing
            Exception: If prediction fails
        """
        try:
            logger.debug(
                "Running ML prediction",
                extra={"features": features, "model_version": self.model_version},
            )

            # Calculate fraud score using rule-based approach
            fraud_score = self._calculate_rule_based_score(features)

            # Determine risk level and recommendation
            risk_level = self._get_risk_level(fraud_score)
            recommendation = self._get_recommendation(risk_level)

            result = {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "model_version": self.model_version,
            }

            logger.debug(
                "ML prediction completed",
                extra={
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "recommendation": recommendation,
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

    def _calculate_rule_based_score(self, features: Dict[str, Any]) -> float:
        """Calculate fraud score using rule-based approach

        This is a placeholder implementation for Day 3.
        Day 6 will replace this with actual ML model prediction.

        Rules:
        - High velocity transactions increase score
        - Large amounts increase score
        - Multiple transactions from same IP increase score

        Args:
            features: Transaction features dict

        Returns:
            Fraud score between 0.0 and 1.0
        """
        score = 0.0

        # Rule 1: Amount-based scoring (0-0.3 points)
        amount = features.get("amount", 0)
        if amount > 10000:
            score += 0.3
        elif amount > 5000:
            score += 0.2
        elif amount > 1000:
            score += 0.1

        # Rule 2: Velocity-based scoring (0-0.4 points)
        transactions_last_hour = features.get("transactions_last_hour", 0)
        if transactions_last_hour > 10:
            score += 0.4
        elif transactions_last_hour > 5:
            score += 0.3
        elif transactions_last_hour > 3:
            score += 0.2

        # Rule 3: Daily transaction amount (0-0.3 points)
        amount_last_day = features.get("amount_last_day", 0)
        if amount_last_day > 50000:
            score += 0.3
        elif amount_last_day > 20000:
            score += 0.2
        elif amount_last_day > 10000:
            score += 0.1

        # Ensure score is between 0 and 1
        score = min(1.0, max(0.0, score))

        return round(score, 4)

    def _get_risk_level(self, fraud_score: float) -> str:
        """Determine risk level from fraud score

        Args:
            fraud_score: Fraud probability (0-1)

        Returns:
            Risk level: LOW, MEDIUM, HIGH, or CRITICAL
        """
        if fraud_score < LOW_RISK_THRESHOLD:
            return "LOW"
        elif fraud_score < MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        elif fraud_score < HIGH_RISK_THRESHOLD:
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
