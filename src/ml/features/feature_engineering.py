"""
Feature engineering orchestrator.
Combines all feature extractors and manages feature extraction pipeline.
"""

from typing import Dict, Any, List
import logging
from .time_features import TimeFeatureExtractor
from .amount_features import AmountFeatureExtractor
from .email_features import EmailFeatureExtractor

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Orchestrates feature extraction from multiple extractors.
    
    Combines features from:
    - Time patterns
    - Transaction amounts
    - Email characteristics
    - Velocity features (from external source)
    
    Total: 70+ features
    """
    
    def __init__(self):
        """Initialize feature engineer with all extractors"""
        self.time_extractor = TimeFeatureExtractor()
        self.amount_extractor = AmountFeatureExtractor()
        self.email_extractor = EmailFeatureExtractor()
        
        logger.info(
            "FeatureEngineer initialized",
            extra={
                "extractors": [
                    "TimeFeatureExtractor",
                    "AmountFeatureExtractor",
                    "EmailFeatureExtractor"
                ]
            }
        )
    
    def extract_all_features(
        self,
        transaction_data: Dict[str, Any],
        velocity_features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract all features from transaction data
        
        Args:
            transaction_data: Transaction data dictionary
            velocity_features: Pre-calculated velocity features (optional)
            
        Returns:
            Dictionary with all extracted features (70+)
        """
        try:
            # Extract features from each extractor
            time_features = self.time_extractor.extract(transaction_data)
            amount_features = self.amount_extractor.extract(transaction_data)
            email_features = self.email_extractor.extract(transaction_data)
            
            # Combine all features
            all_features = {
                **time_features,
                **amount_features,
                **email_features
            }
            
            # Add velocity features if provided
            if velocity_features:
                # Flatten velocity features with prefix
                for key, value in velocity_features.items():
                    all_features[f'velocity_{key}'] = value
            
            # Add basic transaction features
            all_features['currency_PEN'] = int(transaction_data.get('currency', 'PEN') == 'PEN')
            all_features['currency_USD'] = int(transaction_data.get('currency', 'USD') == 'USD')
            
            # Payment method features
            payment_method = transaction_data.get('payment_method', {})
            payment_type = payment_method.get('type', 'unknown')
            all_features['payment_credit_card'] = int(payment_type == 'credit_card')
            all_features['payment_debit_card'] = int(payment_type == 'debit_card')
            all_features['payment_digital_wallet'] = int(payment_type == 'digital_wallet')
            
            # Merchant category features
            merchant = transaction_data.get('merchant', {})
            merchant_category = merchant.get('category', 'unknown')
            all_features['merchant_retail'] = int(merchant_category == 'retail')
            all_features['merchant_ecommerce'] = int(merchant_category == 'e-commerce')
            all_features['merchant_services'] = int(merchant_category == 'services')
            
            feature_count = len(all_features)
            
            logger.info(
                "All features extracted successfully",
                extra={
                    "total_features": feature_count,
                    "time_features": len(time_features),
                    "amount_features": len(amount_features),
                    "email_features": len(email_features),
                    "velocity_features": len(velocity_features) if velocity_features else 0
                }
            )
            
            return all_features
            
        except Exception as e:
            logger.error(
                f"Error extracting features: {str(e)}",
                exc_info=True
            )
            raise
    
    def get_all_feature_names(self) -> List[str]:
        """Get list of all feature names
        
        Returns:
            List of all feature names (70+)
        """
        feature_names = []
        
        # Add features from each extractor
        feature_names.extend(self.time_extractor.get_feature_names())
        feature_names.extend(self.amount_extractor.get_feature_names())
        feature_names.extend(self.email_extractor.get_feature_names())
        
        # Add velocity feature names (example - actual names depend on velocity calculation)
        velocity_feature_names = [
            'velocity_customer_tx_count_1h',
            'velocity_customer_tx_count_24h',
            'velocity_customer_tx_count_7d',
            'velocity_customer_amount_1h',
            'velocity_customer_amount_24h',
            'velocity_customer_amount_7d',
            'velocity_ip_tx_count_1h',
            'velocity_ip_tx_count_24h',
            'velocity_device_tx_count_1h',
            'velocity_device_tx_count_24h'
        ]
        feature_names.extend(velocity_feature_names)
        
        # Add basic transaction features
        feature_names.extend([
            'currency_PEN',
            'currency_USD',
            'payment_credit_card',
            'payment_debit_card',
            'payment_digital_wallet',
            'merchant_retail',
            'merchant_ecommerce',
            'merchant_services'
        ])
        
        return feature_names
    
    def get_feature_count(self) -> int:
        """Get total number of features
        
        Returns:
            Total feature count
        """
        return len(self.get_all_feature_names())
