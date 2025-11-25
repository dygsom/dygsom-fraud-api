"""
Tests for ML feature extractors.
Validates feature extraction functionality.
"""

import pytest
from datetime import datetime
from src.ml.features.time_features import TimeFeatureExtractor
from src.ml.features.amount_features import AmountFeatureExtractor
from src.ml.features.email_features import EmailFeatureExtractor
from src.ml.features.feature_engineering import FeatureEngineer


class TestTimeFeatureExtractor:
    """Tests for TimeFeatureExtractor"""
    
    def test_time_features_extraction(self):
        """Test time feature extraction"""
        extractor = TimeFeatureExtractor()
        
        transaction_data = {
            'timestamp': '2024-01-15T14:30:00'
        }
        
        features = extractor.extract(transaction_data)
        
        # Verify all 8 features are present
        assert len(features) == 8
        assert 'hour_of_day' in features
        assert 'day_of_week' in features
        assert 'is_weekend' in features
        assert 'is_night' in features
        assert 'is_business_hours' in features
        assert 'day_of_month' in features
        assert 'is_month_start' in features
        assert 'is_month_end' in features
        
        # Verify values
        assert features['hour_of_day'] == 14  # 2:30 PM
        assert features['is_business_hours'] == 1  # 14:00 is business hours
        assert features['is_night'] == 0
        assert features['day_of_month'] == 15
    
    def test_weekend_detection(self):
        """Test weekend detection"""
        extractor = TimeFeatureExtractor()
        
        # Saturday
        features = extractor.extract({'timestamp': '2024-01-13T10:00:00'})
        assert features['is_weekend'] == 1
        
        # Monday
        features = extractor.extract({'timestamp': '2024-01-15T10:00:00'})
        assert features['is_weekend'] == 0
    
    def test_night_detection(self):
        """Test night time detection"""
        extractor = TimeFeatureExtractor()
        
        # Night time
        features = extractor.extract({'timestamp': '2024-01-15T23:00:00'})
        assert features['is_night'] == 1
        
        # Day time
        features = extractor.extract({'timestamp': '2024-01-15T12:00:00'})
        assert features['is_night'] == 0


class TestAmountFeatureExtractor:
    """Tests for AmountFeatureExtractor"""
    
    def test_amount_features_extraction(self):
        """Test amount feature extraction"""
        extractor = AmountFeatureExtractor()
        
        transaction_data = {
            'amount': 1500.50
        }
        
        features = extractor.extract(transaction_data)
        
        # Verify all 7 features are present
        assert len(features) == 7
        assert 'amount' in features
        assert 'amount_log' in features
        assert 'amount_rounded' in features
        assert 'amount_decimal_places' in features
        assert 'is_high_value' in features
        assert 'is_very_high_value' in features
        assert 'amount_percentile' in features
        
        # Verify values
        assert features['amount'] == 1500.50
        assert features['is_high_value'] == 1  # > 1000
        assert features['is_very_high_value'] == 0  # <= 5000
        assert features['amount_rounded'] == 0  # Has decimals
    
    def test_round_amount_detection(self):
        """Test round amount detection"""
        extractor = AmountFeatureExtractor()
        
        # Round amount
        features = extractor.extract({'amount': 1000})
        assert features['amount_rounded'] == 1
        
        # Non-round amount
        features = extractor.extract({'amount': 1250.75})
        assert features['amount_rounded'] == 0
    
    def test_high_value_detection(self):
        """Test high value transaction detection"""
        extractor = AmountFeatureExtractor()
        
        # Very high value
        features = extractor.extract({'amount': 6000})
        assert features['is_high_value'] == 1
        assert features['is_very_high_value'] == 1
        
        # High value
        features = extractor.extract({'amount': 2000})
        assert features['is_high_value'] == 1
        assert features['is_very_high_value'] == 0
        
        # Normal value
        features = extractor.extract({'amount': 500})
        assert features['is_high_value'] == 0
        assert features['is_very_high_value'] == 0


class TestEmailFeatureExtractor:
    """Tests for EmailFeatureExtractor"""
    
    def test_email_features_extraction(self):
        """Test email feature extraction"""
        extractor = EmailFeatureExtractor()
        
        transaction_data = {
            'customer': {
                'email': 'john.doe123@gmail.com'
            }
        }
        
        features = extractor.extract(transaction_data)
        
        # Verify all 8 features are present
        assert len(features) == 8
        assert 'email_length' in features
        assert 'email_domain' in features
        assert 'is_disposable_email' in features
        assert 'is_gmail' in features
        assert 'is_yahoo' in features
        assert 'is_corporate_email' in features
        assert 'email_has_numbers' in features
        assert 'email_numeric_ratio' in features
        
        # Verify values
        assert features['email_length'] == len('john.doe123@gmail.com')
        assert features['is_gmail'] == 1
        assert features['is_yahoo'] == 0
        assert features['is_corporate_email'] == 0  # Gmail is not corporate
        assert features['email_has_numbers'] == 1  # Has '123'
    
    def test_disposable_email_detection(self):
        """Test disposable email detection"""
        extractor = EmailFeatureExtractor()
        
        # Disposable email
        features = extractor.extract({
            'customer': {'email': 'test@tempmail.com'}
        })
        assert features['is_disposable_email'] == 1
        
        # Regular email
        features = extractor.extract({
            'customer': {'email': 'test@gmail.com'}
        })
        assert features['is_disposable_email'] == 0
    
    def test_corporate_email_detection(self):
        """Test corporate email detection"""
        extractor = EmailFeatureExtractor()
        
        # Corporate email
        features = extractor.extract({
            'customer': {'email': 'employee@company.com'}
        })
        assert features['is_corporate_email'] == 1
        
        # Free provider
        features = extractor.extract({
            'customer': {'email': 'user@gmail.com'}
        })
        assert features['is_corporate_email'] == 0


class TestFeatureEngineer:
    """Tests for FeatureEngineer"""
    
    def test_feature_engineer_integration(self):
        """Test complete feature engineering pipeline"""
        engineer = FeatureEngineer()
        
        transaction_data = {
            'timestamp': '2024-01-15T14:30:00',
            'amount': 1500.50,
            'currency': 'PEN',
            'customer': {
                'email': 'john.doe@gmail.com'
            },
            'payment_method': {
                'type': 'credit_card'
            },
            'merchant': {
                'category': 'retail'
            }
        }
        
        velocity_features = {
            'customer_tx_count_1h': 2,
            'customer_tx_count_24h': 5,
            'customer_amount_24h': 3000,
            'ip_tx_count_1h': 1,
            'device_tx_count_1h': 2
        }
        
        # Extract all features
        all_features = engineer.extract_all_features(
            transaction_data,
            velocity_features
        )
        
        # Verify comprehensive feature set
        assert len(all_features) > 30  # Should have 30+ features
        
        # Verify time features
        assert 'hour_of_day' in all_features
        assert 'day_of_week' in all_features
        
        # Verify amount features
        assert 'amount' in all_features
        assert 'amount_log' in all_features
        
        # Verify email features
        assert 'email_length' in all_features
        assert 'is_gmail' in all_features
        
        # Verify velocity features
        assert 'velocity_customer_tx_count_1h' in all_features
        assert 'velocity_customer_tx_count_24h' in all_features
        
        # Verify transaction features
        assert 'currency_PEN' in all_features
        assert 'payment_credit_card' in all_features
        assert 'merchant_retail' in all_features
    
    def test_feature_count(self):
        """Test feature count"""
        engineer = FeatureEngineer()
        
        feature_count = engineer.get_feature_count()
        assert feature_count > 30  # Should have 30+ features total
        
        feature_names = engineer.get_all_feature_names()
        assert len(feature_names) == feature_count
        assert len(feature_names) == len(set(feature_names))  # No duplicates
    
    def test_feature_extraction_without_velocity(self):
        """Test feature extraction without velocity features"""
        engineer = FeatureEngineer()
        
        transaction_data = {
            'timestamp': '2024-01-15T14:30:00',
            'amount': 1500,
            'currency': 'PEN',
            'customer': {
                'email': 'test@gmail.com'
            },
            'payment_method': {
                'type': 'credit_card'
            },
            'merchant': {
                'category': 'retail'
            }
        }
        
        # Extract features without velocity
        all_features = engineer.extract_all_features(transaction_data)
        
        # Should still work
        assert len(all_features) > 20
        assert 'hour_of_day' in all_features
        assert 'amount' in all_features


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
