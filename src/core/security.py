"""
Security utilities for API authentication and encryption.
Provides functions for API key generation, hashing, and verification.
"""

import secrets
import hashlib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Constants
API_KEY_PREFIX = "dygsom_"
API_KEY_LENGTH = 32


class SecurityUtils:
    """Security utilities for API key management
    
    Provides methods for generating, hashing, and verifying API keys.
    All keys are hashed with SHA-256 before storage.
    """
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key
        
        Format: dygsom_<32_random_characters>
        Uses cryptographically secure random number generator.
        
        Returns:
            Generated API key in plain text (only shown once)
        """
        random_part = secrets.token_urlsafe(API_KEY_LENGTH)[:API_KEY_LENGTH]
        api_key = f"{API_KEY_PREFIX}{random_part}"
        
        logger.info(
            "API key generated",
            extra={"key_prefix": API_KEY_PREFIX, "length": len(api_key)}
        )
        
        return api_key
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key with SHA-256
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Hexadecimal hash of the API key
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        # Import here to avoid circular imports
        from src.core.config import settings
        
        # Add salt for security (protects against rainbow table attacks)
        salted_key = api_key + settings.API_KEY_SALT
        key_hash = hashlib.sha256(salted_key.encode()).hexdigest()
        
        logger.debug(
            "API key hashed",
            extra={"hash_length": len(key_hash)}
        )
        
        return key_hash
    
    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """Verify API key against stored hash
        
        Uses secrets.compare_digest for constant-time comparison
        to prevent timing attacks.
        
        Args:
            plain_key: Plain text API key from request
            hashed_key: Stored hash from database
            
        Returns:
            True if keys match, False otherwise
        """
        if not plain_key or not hashed_key:
            logger.warning(
                "API key verification failed - empty key",
                extra={"has_plain": bool(plain_key), "has_hash": bool(hashed_key)}
            )
            return False
        
        try:
            computed_hash = SecurityUtils.hash_api_key(plain_key)
            is_valid = secrets.compare_digest(computed_hash, hashed_key)
            
            if is_valid:
                logger.debug("API key verified successfully")
            else:
                logger.warning("API key verification failed - hash mismatch")
            
            return is_valid
            
        except Exception as e:
            logger.error(
                "Error verifying API key",
                extra={"error": str(e)},
                exc_info=True
            )
            return False
    
    @staticmethod
    def generate_and_hash() -> Tuple[str, str]:
        """Generate API key and return both plain and hashed versions
        
        Convenience method for creating new API keys.
        
        Returns:
            Tuple of (plain_key, hashed_key)
        """
        plain_key = SecurityUtils.generate_api_key()
        hashed_key = SecurityUtils.hash_api_key(plain_key)
        
        logger.info("API key generated and hashed")
        
        return plain_key, hashed_key
