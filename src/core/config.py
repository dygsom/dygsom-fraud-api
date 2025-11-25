"""
Centralized configuration using Pydantic Settings.
Loads from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "DYGSOM Fraud API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="NODE_ENV")
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 3000

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # Security
    API_KEY_PREFIX: str = "dygsom_"
    API_KEY_LENGTH: int = 32
    API_KEY_SALT: str = Field(default="change-in-production", env="API_KEY_SALT")
    JWT_SECRET: str = Field(default="change-in-production", env="JWT_SECRET")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    IP_RATE_LIMIT_PER_MINUTE: int = 50

    # Caching
    CACHE_L1_MAX_SIZE: int = 1000
    CACHE_DEFAULT_TTL: int = 60
    CACHE_VELOCITY_TTL: int = 60
    CACHE_IP_HISTORY_TTL: int = 300
    CACHE_CUSTOMER_HISTORY_TTL: int = 60

    # Fraud Detection Business Rules
    FRAUD_MAX_TX_PER_HOUR: int = 5
    FRAUD_MAX_TX_PER_DAY: int = 20
    FRAUD_MAX_AMOUNT_PER_DAY: float = 10000.00
    FRAUD_SCORE_LOW_THRESHOLD: float = 0.3
    FRAUD_SCORE_MEDIUM_THRESHOLD: float = 0.5
    FRAUD_SCORE_HIGH_THRESHOLD: float = 0.8

    # ML Model
    ML_MODEL_VERSION: str = "v2.0.0-xgboost"
    ML_MODEL_PATH: str = "ml/models/fraud_model.joblib"

    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    ENABLE_SWAGGER: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow extra fields from environment
        extra = "ignore"


# Global settings instance - initialized once
settings = Settings()
