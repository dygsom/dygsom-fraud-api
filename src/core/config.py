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
    # Optimized pool settings for high throughput (100+ req/sec)
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        description="Base connection pool size (20 for single instance, 50 for production)"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=30,
        description="Additional connections beyond pool_size under load"
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=10,
        description="Timeout in seconds to wait for a connection from the pool"
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600,
        description="Recycle connections after N seconds to prevent stale connections"
    )
    DATABASE_POOL_PRE_PING: bool = Field(
        default=True,
        description="Test connections before using them (prevents stale connection errors)"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Log all SQL queries (disable in production for performance)"
    )
    DATABASE_QUERY_TIMEOUT: int = Field(
        default=30,
        description="Maximum query execution time in seconds"
    )

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    # Optimized Redis pool settings for L2 cache
    REDIS_MAX_CONNECTIONS: int = Field(
        default=100,
        description="Maximum Redis connections in the pool (100 for high throughput)"
    )
    REDIS_MIN_CONNECTIONS: int = Field(
        default=10,
        description="Minimum idle connections to maintain"
    )
    REDIS_SOCKET_TIMEOUT: int = Field(
        default=2,
        description="Socket timeout in seconds (reduced from 5 for faster failover)"
    )
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(
        default=2,
        description="Connection timeout in seconds"
    )
    REDIS_SOCKET_KEEPALIVE: bool = Field(
        default=True,
        description="Enable TCP keepalive for connection health"
    )
    REDIS_RETRY_ON_TIMEOUT: bool = Field(
        default=True,
        description="Retry once on timeout errors"
    )
    REDIS_DECODE_RESPONSES: bool = Field(
        default=True,
        description="Automatically decode byte responses to strings"
    )

    # Security
    API_KEY_PREFIX: str = "dygsom_"
    API_KEY_LENGTH: int = 32
    API_KEY_SALT: str = Field(default="change-in-production", env="API_KEY_SALT")
    JWT_SECRET: str = Field(default="change-in-production", env="JWT_SECRET")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    IP_RATE_LIMIT_PER_MINUTE: int = 50

    # Caching - Optimized for 90%+ hit rate
    CACHE_L1_MAX_SIZE: int = Field(
        default=2000,
        description="L1 (in-memory) cache max entries (increased from 1000)"
    )
    CACHE_L2_ENABLED: bool = Field(
        default=True,
        description="Enable L2 (Redis) cache"
    )
    CACHE_DEFAULT_TTL: int = Field(
        default=60,
        description="Default cache TTL in seconds"
    )
    CACHE_VELOCITY_TTL: int = Field(
        default=60,
        description="Velocity features cache TTL (matches time window)"
    )
    CACHE_IP_HISTORY_TTL: int = Field(
        default=300,
        description="IP history cache TTL (5 minutes)"
    )
    CACHE_CUSTOMER_HISTORY_TTL: int = Field(
        default=60,
        description="Customer history cache TTL (1 minute)"
    )
    CACHE_ML_PREDICTION_TTL: int = Field(
        default=300,
        description="ML prediction cache TTL (5 minutes)"
    )
    # Cache key prefixes for namespacing
    CACHE_KEY_PREFIX: str = Field(
        default="fraud:",
        description="Global cache key prefix"
    )

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
    ML_BATCH_PREDICTION: bool = Field(
        default=False,
        description="Enable batch prediction mode for higher throughput"
    )
    ML_PREDICTION_TIMEOUT: int = Field(
        default=5,
        description="Maximum ML prediction time in seconds"
    )

    # API Performance Settings
    API_REQUEST_TIMEOUT: int = Field(
        default=30,
        description="Maximum API request processing time in seconds"
    )
    API_WORKER_PROCESSES: int = Field(
        default=4,
        description="Number of Uvicorn worker processes (CPU cores * 2)"
    )
    API_WORKER_CONNECTIONS: int = Field(
        default=1000,
        description="Maximum concurrent connections per worker"
    )
    API_BACKLOG: int = Field(
        default=2048,
        description="Socket backlog size for pending connections"
    )
    API_KEEPALIVE_TIMEOUT: int = Field(
        default=5,
        description="HTTP keepalive timeout in seconds"
    )
    API_GRACEFUL_SHUTDOWN_TIMEOUT: int = Field(
        default=30,
        description="Graceful shutdown timeout in seconds"
    )

    # Performance Optimization Flags
    ENABLE_QUERY_CACHE: bool = Field(
        default=True,
        description="Enable database query result caching"
    )
    ENABLE_CONNECTION_POOLING: bool = Field(
        default=True,
        description="Enable database connection pooling"
    )
    ENABLE_ASYNC_PROCESSING: bool = Field(
        default=True,
        description="Enable async processing for I/O operations"
    )
    ENABLE_GZIP_COMPRESSION: bool = Field(
        default=True,
        description="Enable gzip compression for API responses"
    )
    GZIP_COMPRESSION_LEVEL: int = Field(
        default=6,
        description="Gzip compression level (1-9, 6 is balanced)"
    )
    GZIP_MIN_SIZE: int = Field(
        default=1024,
        description="Minimum response size in bytes to compress"
    )

    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    ENABLE_SWAGGER: bool = True

    # Prometheus Metrics Configuration
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_SCRAPE_INTERVAL: str = "10s"
    GRAFANA_PORT: int = 3001

    # Metric Histogram Buckets (tuples for performance)
    METRIC_REQUEST_DURATION_BUCKETS: tuple = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    METRIC_ML_DURATION_BUCKETS: tuple = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
    METRIC_FEATURE_DURATION_BUCKETS: tuple = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25)
    METRIC_CACHE_DURATION_BUCKETS: tuple = (0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1)
    METRIC_DB_DURATION_BUCKETS: tuple = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
    METRIC_TRANSACTION_AMOUNT_BUCKETS: tuple = (10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 50000)
    METRIC_FRAUD_SCORE_BUCKETS: tuple = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",  # Next.js dashboard
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
