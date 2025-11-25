"""
Amount-based feature extraction.
Extracts features from transaction amounts.
"""

from typing import Dict, Any, List
import math
import logging
from .base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)


class AmountFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts amount-based features from transactions.
    
    Features extracted:
    - amount: Original amount
    - amount_log: Log-transformed amount
    - amount_rounded: Is amount a round number (0/1)
    - amount_decimal_places: Number of decimal places
    - is_high_value: Amount > 1000 PEN (0/1)
    - is_very_high_value: Amount > 5000 PEN (0/1)
    - amount_percentile: Approximate percentile (0-100)
    """
    
    def __init__(self):
        """Initialize amount feature extractor"""
        super().__init__("amount")
        # Typical amount thresholds for percentile estimation
        self.percentile_thresholds = [
            10, 25, 50, 100, 200, 500, 1000, 2000, 5000, 10000
        ]
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract amount features from transaction data
        
        Args:
            transaction_data: Dictionary with 'amount' field
            
        Returns:
            Dictionary with 7 amount features
            
        Raises:
            ValueError: If amount field is missing
        """
        self.validate_data(transaction_data, ['amount'])
        
        try:
            amount = float(transaction_data['amount'])
            
            # Check if amount is negative
            if amount < 0:
                logger.warning(
                    "Negative amount detected",
                    extra={"amount": amount}
                )
                amount = abs(amount)
            
            # Log transform (add 1 to avoid log(0))
            amount_log = math.log1p(amount)
            
            # Check if round number (ends in 0, 00, or 000)
            amount_str = str(amount)
            if '.' in amount_str:
                decimal_part = amount_str.split('.')[1]
                decimal_places = len(decimal_part.rstrip('0'))
            else:
                decimal_places = 0
            
            # Round number if no decimals and ends with zeros
            is_rounded = int(
                decimal_places == 0 and 
                (amount % 10 == 0 or amount % 100 == 0 or amount % 1000 == 0)
            )
            
            # Calculate approximate percentile based on typical distributions
            percentile = 0
            for i, threshold in enumerate(self.percentile_thresholds):
                if amount >= threshold:
                    percentile = (i + 1) * 10
            percentile = min(percentile, 100)
            
            features = {
                'amount': amount,
                'amount_log': amount_log,
                'amount_rounded': is_rounded,
                'amount_decimal_places': decimal_places,
                'is_high_value': int(amount > 1000),
                'is_very_high_value': int(amount > 5000),
                'amount_percentile': percentile
            }
            
            logger.debug(
                "Amount features extracted",
                extra={
                    "feature_count": len(features),
                    "amount": amount,
                    "percentile": percentile
                }
            )
            
            return features
            
        except Exception as e:
            logger.error(
                f"Error extracting amount features: {str(e)}",
                exc_info=True
            )
            # Return default values on error
            return {
                'amount': 0.0,
                'amount_log': 0.0,
                'amount_rounded': 0,
                'amount_decimal_places': 2,
                'is_high_value': 0,
                'is_very_high_value': 0,
                'amount_percentile': 50
            }
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names
        
        Returns:
            List of 7 amount feature names
        """
        return [
            'amount',
            'amount_log',
            'amount_rounded',
            'amount_decimal_places',
            'is_high_value',
            'is_very_high_value',
            'amount_percentile'
        ]
