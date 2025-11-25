"""
Email-based feature extraction.
Extracts features from customer email addresses.
"""

from typing import Dict, Any, List
import re
import logging
from .base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)


class EmailFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts email-based features from customer data.
    
    Features extracted:
    - email_length: Length of email address
    - email_domain: Domain name (hashed for privacy)
    - is_disposable_email: Known disposable email service (0/1)
    - is_gmail: Gmail address (0/1)
    - is_yahoo: Yahoo address (0/1)
    - is_corporate_email: Has company domain (0/1)
    - email_has_numbers: Contains numbers (0/1)
    - email_numeric_ratio: Proportion of numeric characters
    """
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'throwaway.email', 'mailinator.com', 'trashmail.com',
        'maildrop.cc', 'yopmail.com', 'temp-mail.org'
    }
    
    # Free email providers
    FREE_PROVIDERS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'live.com', 'aol.com', 'icloud.com', 'protonmail.com'
    }
    
    def __init__(self):
        """Initialize email feature extractor"""
        super().__init__("email")
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract email features from transaction data
        
        Args:
            transaction_data: Dictionary with 'customer' -> 'email' field
            
        Returns:
            Dictionary with 8 email features
            
        Raises:
            ValueError: If email field is missing
        """
        # Validate nested structure
        if 'customer' not in transaction_data:
            raise ValueError("Missing 'customer' field in transaction data")
        if 'email' not in transaction_data['customer']:
            raise ValueError("Missing 'email' field in customer data")
        
        try:
            email = transaction_data['customer']['email'].lower().strip()
            
            # Extract domain
            if '@' in email:
                local_part, domain = email.split('@', 1)
            else:
                logger.warning(f"Invalid email format: {email}")
                local_part = email
                domain = "unknown.com"
            
            # Email length
            email_length = len(email)
            
            # Check disposable email
            is_disposable = int(domain in self.DISPOSABLE_DOMAINS)
            
            # Check specific providers
            is_gmail = int(domain == 'gmail.com')
            is_yahoo = int(domain == 'yahoo.com')
            
            # Corporate email (not in free provider list and has proper domain)
            is_corporate = int(
                domain not in self.FREE_PROVIDERS and
                domain not in self.DISPOSABLE_DOMAINS and
                '.' in domain and
                len(domain) > 5
            )
            
            # Count numbers in email
            numbers_in_email = sum(c.isdigit() for c in local_part)
            email_has_numbers = int(numbers_in_email > 0)
            
            # Numeric ratio (numbers / total characters in local part)
            email_numeric_ratio = numbers_in_email / len(local_part) if len(local_part) > 0 else 0.0
            
            # Domain hash (for categorical encoding)
            domain_hash = hash(domain) % 10000  # Simple hash for domain
            
            features = {
                'email_length': email_length,
                'email_domain': domain_hash,
                'is_disposable_email': is_disposable,
                'is_gmail': is_gmail,
                'is_yahoo': is_yahoo,
                'is_corporate_email': is_corporate,
                'email_has_numbers': email_has_numbers,
                'email_numeric_ratio': round(email_numeric_ratio, 4)
            }
            
            logger.debug(
                "Email features extracted",
                extra={
                    "feature_count": len(features),
                    "email_length": email_length,
                    "domain": domain,
                    "is_corporate": is_corporate
                }
            )
            
            return features
            
        except Exception as e:
            logger.error(
                f"Error extracting email features: {str(e)}",
                exc_info=True
            )
            # Return default values on error
            return {
                'email_length': 20,
                'email_domain': 0,
                'is_disposable_email': 0,
                'is_gmail': 0,
                'is_yahoo': 0,
                'is_corporate_email': 0,
                'email_has_numbers': 0,
                'email_numeric_ratio': 0.0
            }
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names
        
        Returns:
            List of 8 email feature names
        """
        return [
            'email_length',
            'email_domain',
            'is_disposable_email',
            'is_gmail',
            'is_yahoo',
            'is_corporate_email',
            'email_has_numbers',
            'email_numeric_ratio'
        ]
