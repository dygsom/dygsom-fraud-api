"""
Model Manager for fraud detection ML models.

Handles loading, validation, and prediction with trained models.
Provides fallback strategies when models are unavailable.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import joblib
import xgboost as xgb
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages ML models for fraud detection.
    
    Handles:
    - Model loading from disk
    - Model validation
    - Predictions with error handling
    - Fallback strategies
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize model manager
        
        Args:
            model_path: Path to trained model file. If None, uses default path.
        """
        self.model_path = model_path or "ml/models/fraud_model.joblib"
        self.model: Optional[xgb.XGBClassifier] = None
        self.model_loaded = False
        self.model_metadata: Dict[str, Any] = {}
        
        logger.info(
            "ModelManager initialized",
            extra={"model_path": self.model_path}
        )
    
    def load_model(self) -> bool:
        """Load model from disk
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            model_file = Path(self.model_path)
            
            if not model_file.exists():
                logger.warning(
                    f"Model file not found: {model_file}",
                    extra={"path": str(model_file.absolute())}
                )
                return False
            
            # Load model
            self.model = joblib.load(model_file)
            
            # Validate model
            if not isinstance(self.model, xgb.XGBClassifier):
                logger.error("Loaded object is not an XGBoost classifier")
                self.model = None
                return False
            
            # Store metadata
            self.model_metadata = {
                'loaded_at': datetime.now().isoformat(),
                'model_file': str(model_file.absolute()),
                'n_features': self.model.n_features_in_ if hasattr(self.model, 'n_features_in_') else None,
                'model_type': type(self.model).__name__
            }
            
            self.model_loaded = True
            
            logger.info(
                "Model loaded successfully",
                extra=self.model_metadata
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Error loading model: {str(e)}",
                exc_info=True
            )
            self.model = None
            self.model_loaded = False
            return False
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud probability for given features
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Dictionary with prediction results:
            - fraud_probability: Probability of fraud (0-1)
            - fraud_score: Scaled fraud score (0-100)
            - prediction: Binary prediction (0/1)
            - model_used: Whether ML model was used
        """
        # Ensure model is loaded
        if not self.model_loaded:
            success = self.load_model()
            if not success:
                logger.warning("Model not available, using fallback")
                return self._fallback_prediction(features)
        
        try:
            # Convert features to array
            feature_array = self._features_to_array(features)
            
            # Make prediction
            fraud_probability = float(self.model.predict_proba(feature_array)[0, 1])
            prediction = int(self.model.predict(feature_array)[0])
            
            # Scale to 0-100
            fraud_score = fraud_probability * 100
            
            result = {
                'fraud_probability': round(fraud_probability, 4),
                'fraud_score': round(fraud_score, 2),
                'prediction': prediction,
                'model_used': True,
                'confidence': self._calculate_confidence(fraud_probability)
            }
            
            logger.debug(
                "Prediction made",
                extra={
                    "fraud_score": result['fraud_score'],
                    "prediction": result['prediction']
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error making prediction: {str(e)}",
                exc_info=True
            )
            return self._fallback_prediction(features)
    
    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to numpy array
        
        Args:
            features: Dictionary of features
            
        Returns:
            Numpy array with features in correct order
        """
        # Remove non-feature fields
        feature_dict = {
            k: v for k, v in features.items()
            if k not in ['transaction_id', 'is_fraud']
        }
        
        # Sort keys to ensure consistent order
        sorted_keys = sorted(feature_dict.keys())
        feature_values = [feature_dict[k] for k in sorted_keys]
        
        # Convert to 2D array (1 sample)
        return np.array([feature_values])
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calculate confidence level based on probability
        
        Args:
            probability: Fraud probability (0-1)
            
        Returns:
            Confidence level string
        """
        # Distance from decision boundary (0.5)
        distance = abs(probability - 0.5)
        
        if distance >= 0.4:
            return "HIGH"
        elif distance >= 0.2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _fallback_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction using rule-based approach
        
        Args:
            features: Dictionary of features
            
        Returns:
            Dictionary with fallback prediction
        """
        logger.info("Using fallback prediction (rule-based)")
        
        # Simple rule-based scoring
        score = 0.0
        
        # High value transactions
        if features.get('is_very_high_value', 0) == 1:
            score += 30
        elif features.get('is_high_value', 0) == 1:
            score += 15
        
        # Night transactions
        if features.get('is_night', 0) == 1:
            score += 10
        
        # Weekend transactions
        if features.get('is_weekend', 0) == 1:
            score += 5
        
        # Disposable email
        if features.get('is_disposable_email', 0) == 1:
            score += 25
        
        # Round amounts (potential fraud indicator)
        if features.get('amount_rounded', 0) == 1:
            score += 10
        
        # High velocity
        velocity_tx_24h = features.get('velocity_customer_tx_count_24h', 0)
        if velocity_tx_24h > 10:
            score += 20
        elif velocity_tx_24h > 5:
            score += 10
        
        # Cap at 100
        score = min(score, 100)
        
        fraud_probability = score / 100
        prediction = int(fraud_probability >= 0.7)
        
        return {
            'fraud_probability': round(fraud_probability, 4),
            'fraud_score': round(score, 2),
            'prediction': prediction,
            'model_used': False,
            'confidence': 'LOW'  # Always low confidence for rule-based
        }
    
    def validate_features(self, features: Dict[str, Any]) -> bool:
        """Validate that features match model requirements
        
        Args:
            features: Dictionary of features
            
        Returns:
            True if features are valid
        """
        if not self.model_loaded:
            logger.warning("Cannot validate features - model not loaded")
            return False
        
        try:
            # Check feature count
            expected_features = self.model.n_features_in_ if hasattr(self.model, 'n_features_in_') else None
            
            # Remove non-feature fields
            feature_count = len([k for k in features.keys() if k not in ['transaction_id', 'is_fraud']])
            
            if expected_features and feature_count != expected_features:
                logger.warning(
                    f"Feature count mismatch: expected {expected_features}, got {feature_count}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating features: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metadata
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_loaded': self.model_loaded,
            'model_path': self.model_path,
            'metadata': self.model_metadata
        }
