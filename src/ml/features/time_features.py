"""
Time-based feature extraction.
Extracts temporal patterns from transaction timestamps.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
from .base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)


class TimeFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts time-based features from transaction timestamps.
    
    Features extracted:
    - hour_of_day: Hour (0-23)
    - day_of_week: Day of week (0=Monday, 6=Sunday)
    - is_weekend: Weekend indicator (0/1)
    - is_night: Night time indicator (22:00-06:00)
    - is_business_hours: Business hours indicator (09:00-18:00)
    - day_of_month: Day of month (1-31)
    - is_month_start: First 3 days of month (0/1)
    - is_month_end: Last 3 days of month (0/1)
    """
    
    def __init__(self):
        """Initialize time feature extractor"""
        super().__init__("time")
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time features from transaction data
        
        Args:
            transaction_data: Dictionary with 'timestamp' field
            
        Returns:
            Dictionary with 8 time features
            
        Raises:
            ValueError: If timestamp field is missing
        """
        self.validate_data(transaction_data, ['timestamp'])
        
        try:
            # Parse timestamp
            timestamp_str = transaction_data['timestamp']
            if isinstance(timestamp_str, str):
                # Try ISO format first
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback to strptime
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
            else:
                timestamp = timestamp_str
            
            # Extract features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            day_of_month = timestamp.day
            
            # Calculate last day of month
            if timestamp.month == 12:
                next_month = timestamp.replace(year=timestamp.year + 1, month=1, day=1)
            else:
                next_month = timestamp.replace(month=timestamp.month + 1, day=1)
            last_day = (next_month - timestamp.replace(day=1)).days
            
            features = {
                'hour_of_day': hour,
                'day_of_week': day_of_week,
                'is_weekend': int(day_of_week >= 5),  # Saturday=5, Sunday=6
                'is_night': int(hour >= 22 or hour < 6),  # 22:00-06:00
                'is_business_hours': int(9 <= hour < 18),  # 09:00-18:00
                'day_of_month': day_of_month,
                'is_month_start': int(day_of_month <= 3),  # First 3 days
                'is_month_end': int(day_of_month >= last_day - 2)  # Last 3 days
            }
            
            logger.debug(
                "Time features extracted",
                extra={
                    "feature_count": len(features),
                    "hour": hour,
                    "day_of_week": day_of_week
                }
            )
            
            return features
            
        except Exception as e:
            logger.error(
                f"Error extracting time features: {str(e)}",
                exc_info=True
            )
            # Return default values on error
            return {
                'hour_of_day': 12,
                'day_of_week': 2,
                'is_weekend': 0,
                'is_night': 0,
                'is_business_hours': 1,
                'day_of_month': 15,
                'is_month_start': 0,
                'is_month_end': 0
            }
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names
        
        Returns:
            List of 8 time feature names
        """
        return [
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_night',
            'is_business_hours',
            'day_of_month',
            'is_month_start',
            'is_month_end'
        ]
