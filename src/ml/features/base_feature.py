"""
Base feature extractor abstract class.
All feature extractors must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaseFeatureExtractor(ABC):
    """
    Abstract base class for all feature extractors.
    
    Provides common interface for extracting features from transaction data.
    All concrete feature extractors must implement the extract() method.
    """
    
    def __init__(self, name: str):
        """Initialize feature extractor
        
        Args:
            name: Name of the feature extractor (e.g., "time", "amount")
        """
        self.name = name
        logger.debug(f"Initialized {self.name} feature extractor")
    
    @abstractmethod
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from transaction data
        
        Args:
            transaction_data: Dictionary with transaction fields
            
        Returns:
            Dictionary with extracted features
            
        Raises:
            ValueError: If required fields are missing
        """
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Get list of feature names this extractor produces
        
        Returns:
            List of feature names
        """
        pass
    
    def validate_data(self, transaction_data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present in transaction data
        
        Args:
            transaction_data: Transaction data dictionary
            required_fields: List of required field names
            
        Raises:
            ValueError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in transaction_data]
        
        if missing_fields:
            error_msg = f"{self.name} extractor missing required fields: {missing_fields}"
            logger.error(error_msg, extra={"missing_fields": missing_fields})
            raise ValueError(error_msg)
        
        logger.debug(
            f"{self.name} data validation passed",
            extra={"required_fields": required_fields}
        )
