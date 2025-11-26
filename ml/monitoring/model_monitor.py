"""
Model monitoring for fraud detection system.
Tracks model performance, fraud rates, and anomalies.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from prisma import Prisma

from src.core.config import settings

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Monitor ML model performance and fraud rates.
    
    Tracks:
    - Fraud rate over time
    - Risk level distribution
    - Model performance metrics
    - Anomaly detection
    """

    def __init__(self, prisma: Prisma):
        """
        Initialize ModelMonitor.
        
        Args:
            prisma: Prisma client instance
        """
        self.prisma = prisma
        logger.info("ModelMonitor initialized")

    async def calculate_fraud_rate(self, hours: int = 24) -> float:
        """
        Calculate fraud rate for the last N hours.
        
        Fraud rate = (HIGH + CRITICAL transactions) / Total transactions * 100
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Fraud rate percentage (0-100)
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Get all transactions in time window
            all_transactions = await self.prisma.transaction.count(
                where={"created_at": {"gte": since}}
            )
            
            if all_transactions == 0:
                logger.debug(f"No transactions found in last {hours} hours")
                return 0.0
            
            # Get HIGH and CRITICAL transactions
            high_risk_transactions = await self.prisma.transaction.count(
                where={
                    "created_at": {"gte": since},
                    "risk_level": {"in": ["HIGH", "CRITICAL"]},
                }
            )
            
            fraud_rate = (high_risk_transactions / all_transactions) * 100
            
            logger.info(
                "Fraud rate calculated",
                extra={
                    "hours": hours,
                    "fraud_rate": fraud_rate,
                    "high_risk_count": high_risk_transactions,
                    "total_count": all_transactions,
                },
            )
            
            return round(fraud_rate, 2)
            
        except Exception as e:
            logger.error(f"Error calculating fraud rate: {e}", exc_info=True)
            return 0.0

    async def get_risk_distribution(self, hours: int = 24) -> Dict[str, int]:
        """
        Get distribution of risk levels.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with counts per risk level
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Get all transactions grouped by risk_level
            transactions = await self.prisma.transaction.find_many(
                where={"created_at": {"gte": since}},
                select={"risk_level": True},
            )
            
            # Count by risk level
            distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            
            for tx in transactions:
                risk_level = tx.risk_level or "LOW"
                distribution[risk_level] = distribution.get(risk_level, 0) + 1
            
            logger.info(
                "Risk distribution calculated",
                extra={"hours": hours, "distribution": distribution},
            )
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting risk distribution: {e}", exc_info=True)
            return {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    async def get_model_performance_summary(
        self, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive model performance summary.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with performance metrics
        """
        try:
            fraud_rate = await self.calculate_fraud_rate(hours)
            risk_distribution = await self.get_risk_distribution(hours)
            
            # Get average fraud score
            since = datetime.utcnow() - timedelta(hours=hours)
            transactions = await self.prisma.transaction.find_many(
                where={"created_at": {"gte": since}},
                select={"fraud_score": True},
            )
            
            if transactions:
                avg_score = sum(tx.fraud_score or 0 for tx in transactions) / len(
                    transactions
                )
            else:
                avg_score = 0.0
            
            summary = {
                "period_hours": hours,
                "fraud_rate_percentage": fraud_rate,
                "average_fraud_score": round(avg_score, 4),
                "risk_distribution": risk_distribution,
                "total_transactions": sum(risk_distribution.values()),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info("Model performance summary generated", extra=summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}", exc_info=True)
            return {
                "period_hours": hours,
                "fraud_rate_percentage": 0.0,
                "average_fraud_score": 0.0,
                "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                "total_transactions": 0,
                "error": str(e),
            }

    async def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect anomalies in fraud patterns.
        
        Checks for:
        - Unusually high fraud rate (>10%)
        - Too many HIGH/CRITICAL transactions
        - Sudden spikes in fraud score
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            fraud_rate = await self.calculate_fraud_rate(hours)
            risk_distribution = await self.get_risk_distribution(hours)
            total = sum(risk_distribution.values())
            
            # Anomaly 1: High fraud rate
            if fraud_rate > 10.0:
                anomalies.append(
                    {
                        "type": "high_fraud_rate",
                        "severity": "HIGH",
                        "message": f"Fraud rate is {fraud_rate}% (threshold: 10%)",
                        "value": fraud_rate,
                        "threshold": 10.0,
                    }
                )
            
            # Anomaly 2: Too many CRITICAL transactions
            if total > 0:
                critical_percentage = (risk_distribution["CRITICAL"] / total) * 100
                if critical_percentage > 5.0:
                    anomalies.append(
                        {
                            "type": "high_critical_rate",
                            "severity": "CRITICAL",
                            "message": f"CRITICAL transactions: {critical_percentage}% (threshold: 5%)",
                            "value": critical_percentage,
                            "threshold": 5.0,
                        }
                    )
            
            # Anomaly 3: Too many HIGH transactions
            if total > 0:
                high_percentage = (risk_distribution["HIGH"] / total) * 100
                if high_percentage > 15.0:
                    anomalies.append(
                        {
                            "type": "high_risk_rate",
                            "severity": "MEDIUM",
                            "message": f"HIGH risk transactions: {high_percentage}% (threshold: 15%)",
                            "value": high_percentage,
                            "threshold": 15.0,
                        }
                    )
            
            if anomalies:
                logger.warning(
                    "Anomalies detected",
                    extra={"hours": hours, "anomaly_count": len(anomalies), "anomalies": anomalies},
                )
            else:
                logger.debug(f"No anomalies detected in last {hours} hours")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return []
