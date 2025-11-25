"""
Cache Repository for caching transaction-related data.
Provides high-level caching methods for fraud detection features.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import logging
from src.core.cache import CacheService
from src.core.config import settings

logger = logging.getLogger(__name__)


class CacheRepository:
    """
    Repository for caching fraud detection features.
    
    Provides methods to cache velocity checks, IP history,
    and customer history with appropriate TTLs.
    """
    
    def __init__(self, cache_service: CacheService):
        """Initialize cache repository
        
        Args:
            cache_service: CacheService instance
        """
        self.cache_service = cache_service
        logger.info("CacheRepository initialized")
    
    async def get_velocity_features(
        self, 
        customer_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached velocity features for customer.
        
        Key format: velocity:{email}:{minute_bucket}
        Where minute_bucket = current_timestamp // 60
        
        Args:
            customer_email: Customer email
            
        Returns:
            Dict with velocity features if cached, None otherwise
        """
        try:
            # Generate cache key with time bucket (1 minute)
            cache_key = self._generate_cache_key(
                prefix="velocity",
                identifier=customer_email,
                time_bucket_seconds=60
            )
            
            # Get from cache
            result = await self.cache_service.get(cache_key)
            
            if result:
                logger.debug(
                    "Velocity features cache hit",
                    extra={"customer_email": customer_email}
                )
            else:
                logger.debug(
                    "Velocity features cache miss",
                    extra={"customer_email": customer_email}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error getting velocity features from cache",
                extra={"customer_email": customer_email, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def set_velocity_features(
        self,
        customer_email: str,
        features: Dict[str, Any]
    ) -> bool:
        """
        Cache velocity features for customer.
        
        Args:
            customer_email: Customer email
            features: Velocity features dict
            
        Returns:
            True if cached successfully
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                prefix="velocity",
                identifier=customer_email,
                time_bucket_seconds=60
            )
            
            # Set in cache with TTL
            result = await self.cache_service.set(
                key=cache_key,
                value=features,
                ttl=settings.CACHE_VELOCITY_TTL
            )
            
            if result:
                logger.debug(
                    "Velocity features cached",
                    extra={"customer_email": customer_email}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error caching velocity features",
                extra={"customer_email": customer_email, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def get_ip_history(
        self,
        ip_address: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached IP history (5-minute buckets)
        
        Args:
            ip_address: IP address
            
        Returns:
            List of recent transactions from IP if cached, None otherwise
        """
        try:
            # Generate cache key with time bucket (5 minutes)
            cache_key = self._generate_cache_key(
                prefix="ip_history",
                identifier=ip_address,
                time_bucket_seconds=300
            )
            
            # Get from cache
            result = await self.cache_service.get(cache_key)
            
            if result:
                logger.debug(
                    "IP history cache hit",
                    extra={"ip_address": ip_address}
                )
            else:
                logger.debug(
                    "IP history cache miss",
                    extra={"ip_address": ip_address}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error getting IP history from cache",
                extra={"ip_address": ip_address, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def set_ip_history(
        self,
        ip_address: str,
        history: List[Dict[str, Any]]
    ) -> bool:
        """Cache IP history
        
        Args:
            ip_address: IP address
            history: List of recent transactions from IP
            
        Returns:
            True if cached successfully
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                prefix="ip_history",
                identifier=ip_address,
                time_bucket_seconds=300
            )
            
            # Set in cache with TTL
            result = await self.cache_service.set(
                key=cache_key,
                value=history,
                ttl=settings.CACHE_IP_HISTORY_TTL
            )
            
            if result:
                logger.debug(
                    "IP history cached",
                    extra={"ip_address": ip_address}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error caching IP history",
                extra={"ip_address": ip_address, "error": str(e)},
                exc_info=True
            )
            return False
    
    async def get_customer_history(
        self,
        customer_email: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached customer transaction history
        
        Args:
            customer_email: Customer email
            
        Returns:
            List of recent customer transactions if cached, None otherwise
        """
        try:
            # Generate cache key with time bucket (1 minute)
            cache_key = self._generate_cache_key(
                prefix="customer_history",
                identifier=customer_email,
                time_bucket_seconds=60
            )
            
            # Get from cache
            result = await self.cache_service.get(cache_key)
            
            if result:
                logger.debug(
                    "Customer history cache hit",
                    extra={"customer_email": customer_email}
                )
            else:
                logger.debug(
                    "Customer history cache miss",
                    extra={"customer_email": customer_email}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error getting customer history from cache",
                extra={"customer_email": customer_email, "error": str(e)},
                exc_info=True
            )
            return None
    
    async def set_customer_history(
        self,
        customer_email: str,
        history: List[Dict[str, Any]]
    ) -> bool:
        """Cache customer transaction history
        
        Args:
            customer_email: Customer email
            history: List of recent customer transactions
            
        Returns:
            True if cached successfully
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                prefix="customer_history",
                identifier=customer_email,
                time_bucket_seconds=60
            )
            
            # Set in cache with TTL
            result = await self.cache_service.set(
                key=cache_key,
                value=history,
                ttl=settings.CACHE_CUSTOMER_HISTORY_TTL
            )
            
            if result:
                logger.debug(
                    "Customer history cached",
                    extra={"customer_email": customer_email}
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error caching customer history",
                extra={"customer_email": customer_email, "error": str(e)},
                exc_info=True
            )
            return False
    
    def _generate_cache_key(
        self,
        prefix: str,
        identifier: str,
        time_bucket_seconds: Optional[int] = None
    ) -> str:
        """
        Generate cache key with optional time bucketing.
        
        Args:
            prefix: Key prefix (e.g., "velocity", "ip_history")
            identifier: Main identifier (email or IP)
            time_bucket_seconds: Bucket size in seconds (optional)
            
        Returns:
            Cache key string
        """
        try:
            # Build base key
            if time_bucket_seconds:
                # Calculate time bucket
                current_timestamp = int(datetime.utcnow().timestamp())
                bucket = current_timestamp // time_bucket_seconds
                key = f"{prefix}:{identifier}:{bucket}"
            else:
                key = f"{prefix}:{identifier}"
            
            # Hash if too long (>250 chars)
            if len(key) > 250:
                key_hash = hashlib.sha256(key.encode()).hexdigest()
                key = f"{prefix}:hash:{key_hash}"
            
            return key
            
        except Exception as e:
            logger.error(
                "Error generating cache key",
                extra={"prefix": prefix, "identifier": identifier, "error": str(e)},
                exc_info=True
            )
            raise
