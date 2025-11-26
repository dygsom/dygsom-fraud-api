"""
Prometheus metrics for monitoring.
Provides 50+ metrics for API, ML, business, cache, and database.
"""

import time
import logging
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from src.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# API METRICS
# ============================================================================

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status", "api_key_name"],
)

REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=settings.METRIC_REQUEST_DURATION_BUCKETS,
)

REQUEST_ERRORS = Counter(
    "api_request_errors_total",
    "Total API request errors",
    ["error_type", "endpoint"],
)

# ============================================================================
# ML METRICS
# ============================================================================

FRAUD_SCORE_DISTRIBUTION = Histogram(
    "fraud_score_distribution",
    "Distribution of fraud scores (0-1)",
    buckets=settings.METRIC_FRAUD_SCORE_BUCKETS,
)

PREDICTIONS_TOTAL = Counter(
    "ml_predictions_total",
    "Total ML predictions",
    ["model_version", "risk_level", "recommendation"],
)

ML_PREDICTION_DURATION = Histogram(
    "ml_prediction_duration_seconds",
    "ML prediction duration in seconds",
    ["model_version"],
    buckets=settings.METRIC_ML_DURATION_BUCKETS,
)

FEATURE_EXTRACTION_DURATION = Histogram(
    "feature_extraction_duration_seconds",
    "Feature extraction duration in seconds",
    ["feature_type"],
    buckets=settings.METRIC_FEATURE_DURATION_BUCKETS,
)

ML_PREDICTION_ERRORS = Counter(
    "ml_prediction_errors_total",
    "ML prediction errors",
    ["model_version", "error_type"],
)

MODEL_INFO = Gauge(
    "ml_model_info",
    "ML model information",
    ["model_version", "model_type"],
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

FRAUD_RATE = Gauge(
    "fraud_rate_percentage",
    "Current fraud rate percentage (sliding window)",
)

RISK_LEVEL_DISTRIBUTION = Counter(
    "risk_level_distribution_total",
    "Distribution of risk levels",
    ["risk_level"],
)

RECOMMENDATION_DISTRIBUTION = Counter(
    "recommendation_distribution_total",
    "Distribution of recommendations",
    ["recommendation"],
)

TRANSACTION_VOLUME = Counter(
    "transaction_volume_total",
    "Total transaction volume",
    ["currency", "risk_level"],
)

TRANSACTION_AMOUNT = Histogram(
    "transaction_amount_distribution",
    "Distribution of transaction amounts",
    ["currency"],
    buckets=settings.METRIC_TRANSACTION_AMOUNT_BUCKETS,
)

# ============================================================================
# CACHE METRICS
# ============================================================================

CACHE_HITS = Counter(
    "cache_hits_total",
    "Cache hits",
    ["layer", "cache_type"],
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Cache misses",
    ["layer", "cache_type"],
)

CACHE_LATENCY = Histogram(
    "cache_latency_seconds",
    "Cache operation latency",
    ["operation", "layer"],
    buckets=settings.METRIC_CACHE_DURATION_BUCKETS,
)

CACHE_SIZE = Gauge(
    "cache_size_bytes",
    "Current cache size in bytes",
    ["layer", "cache_type"],
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["query_type", "table"],
    buckets=settings.METRIC_DB_DURATION_BUCKETS,
)

DB_CONNECTIONS = Gauge(
    "db_connections_active",
    "Active database connections",
)

DB_ERRORS = Counter(
    "db_errors_total",
    "Database errors",
    ["error_type", "table"],
)

DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Database connection pool size",
)

# ============================================================================
# RATE LIMITING METRICS
# ============================================================================

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Rate limit hits",
    ["api_key_name"],
)

RATE_LIMIT_REMAINING = Gauge(
    "rate_limit_remaining",
    "Remaining rate limit quota",
    ["api_key_name"],
)

# ============================================================================
# FEATURE ENGINEERING METRICS
# ============================================================================

FEATURE_COUNT = Gauge(
    "feature_count_total",
    "Total features extracted",
    ["feature_extractor"],
)

FEATURE_NULL_COUNT = Counter(
    "feature_null_count_total",
    "Null features encountered",
    ["feature_name"],
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def track_request(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
    api_key_name: str = "unknown",
) -> None:
    """
    Track API request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status: HTTP status code
        duration: Request duration in seconds
        api_key_name: API key identifier
    """
    try:
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(status),
            api_key_name=api_key_name,
        ).inc()

        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        logger.debug(
            "Request metrics tracked",
            extra={
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "duration_ms": duration * 1000,
                "api_key_name": api_key_name,
            },
        )
    except Exception as e:
        logger.error(f"Error tracking request metrics: {e}")


def track_prediction(
    model_version: str,
    fraud_score: float,
    risk_level: str,
    recommendation: str,
    duration: float,
) -> None:
    """
    Track ML prediction metrics.

    Args:
        model_version: Model version used
        fraud_score: Fraud score (0-1)
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        recommendation: Recommendation (APPROVE, REVIEW, REJECT)
        duration: Prediction duration in seconds
    """
    try:
        FRAUD_SCORE_DISTRIBUTION.observe(fraud_score)

        PREDICTIONS_TOTAL.labels(
            model_version=model_version,
            risk_level=risk_level,
            recommendation=recommendation,
        ).inc()

        ML_PREDICTION_DURATION.labels(model_version=model_version).observe(duration)

        RISK_LEVEL_DISTRIBUTION.labels(risk_level=risk_level).inc()

        RECOMMENDATION_DISTRIBUTION.labels(recommendation=recommendation).inc()

        logger.debug(
            "Prediction metrics tracked",
            extra={
                "model_version": model_version,
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "duration_ms": duration * 1000,
            },
        )
    except Exception as e:
        logger.error(f"Error tracking prediction metrics: {e}")


def track_transaction(amount: float, currency: str, risk_level: str) -> None:
    """
    Track transaction business metrics.

    Args:
        amount: Transaction amount
        currency: Currency code (USD, EUR, etc.)
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
    """
    try:
        TRANSACTION_VOLUME.labels(currency=currency, risk_level=risk_level).inc()

        TRANSACTION_AMOUNT.labels(currency=currency).observe(amount)

        logger.debug(
            "Transaction metrics tracked",
            extra={"amount": amount, "currency": currency, "risk_level": risk_level},
        )
    except Exception as e:
        logger.error(f"Error tracking transaction metrics: {e}")


def track_cache(layer: str, cache_type: str, hit: bool, duration: float) -> None:
    """
    Track cache metrics.

    Args:
        layer: Cache layer (L1, L2)
        cache_type: Cache type (features, velocity, etc.)
        hit: Whether cache hit occurred
        duration: Cache operation duration in seconds
    """
    try:
        if hit:
            CACHE_HITS.labels(layer=layer, cache_type=cache_type).inc()
        else:
            CACHE_MISSES.labels(layer=layer, cache_type=cache_type).inc()

        operation = "hit" if hit else "miss"
        CACHE_LATENCY.labels(operation=operation, layer=layer).observe(duration)

        logger.debug(
            "Cache metrics tracked",
            extra={
                "layer": layer,
                "cache_type": cache_type,
                "hit": hit,
                "duration_ms": duration * 1000,
            },
        )
    except Exception as e:
        logger.error(f"Error tracking cache metrics: {e}")


def track_db_query(query_type: str, table: str, duration: float) -> None:
    """
    Track database query metrics.

    Args:
        query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration: Query duration in seconds
    """
    try:
        DB_QUERY_DURATION.labels(query_type=query_type, table=table).observe(duration)

        logger.debug(
            "DB query metrics tracked",
            extra={
                "query_type": query_type,
                "table": table,
                "duration_ms": duration * 1000,
            },
        )
    except Exception as e:
        logger.error(f"Error tracking DB query metrics: {e}")


def track_feature_extraction(feature_type: str, duration: float) -> None:
    """
    Track feature extraction metrics.

    Args:
        feature_type: Feature type (velocity, amount, device, etc.)
        duration: Extraction duration in seconds
    """
    try:
        FEATURE_EXTRACTION_DURATION.labels(feature_type=feature_type).observe(duration)

        logger.debug(
            "Feature extraction metrics tracked",
            extra={"feature_type": feature_type, "duration_ms": duration * 1000},
        )
    except Exception as e:
        logger.error(f"Error tracking feature extraction metrics: {e}")


def set_model_info(model_version: str, model_type: str) -> None:
    """
    Set ML model information metric.

    Args:
        model_version: Model version string (e.g., "v2.0.0-xgboost")
        model_type: Model type (e.g., "xgboost", "sklearn")
    """
    try:
        # Set gauge to 1 for this model version/type combination
        MODEL_INFO.labels(
            model_version=model_version,
            model_type=model_type
        ).set(1)

        logger.info(
            "Model info metric set",
            extra={
                "model_version": model_version,
                "model_type": model_type
            }
        )
    except Exception as e:
        logger.error(f"Error setting model info metric: {e}", exc_info=True)


def track_ml_error(model_version: str, error_type: str) -> None:
    """
    Track ML prediction errors.

    Args:
        model_version: Model version
        error_type: Error type
    """
    try:
        ML_PREDICTION_ERRORS.labels(
            model_version=model_version, error_type=error_type
        ).inc()

        logger.debug(
            "ML error tracked",
            extra={"model_version": model_version, "error_type": error_type},
        )
    except Exception as e:
        logger.error(f"Error tracking ML error metrics: {e}")


def track_rate_limit(api_key_name: str, remaining: int) -> None:
    """
    Track rate limiting metrics.

    Args:
        api_key_name: API key identifier
        remaining: Remaining quota
    """
    try:
        RATE_LIMIT_HITS.labels(api_key_name=api_key_name).inc()
        RATE_LIMIT_REMAINING.labels(api_key_name=api_key_name).set(remaining)

        logger.debug(
            "Rate limit metrics tracked",
            extra={"api_key_name": api_key_name, "remaining": remaining},
        )
    except Exception as e:
        logger.error(f"Error tracking rate limit metrics: {e}")


def set_model_info(model_version: str, model_type: str) -> None:
    """
    Set ML model information.

    Args:
        model_version: Model version
        model_type: Model type (xgboost, etc.)
    """
    try:
        MODEL_INFO.labels(model_version=model_version, model_type=model_type).set(1)

        logger.info(
            "Model info set",
            extra={"model_version": model_version, "model_type": model_type},
        )
    except Exception as e:
        logger.error(f"Error setting model info: {e}")


def update_fraud_rate(fraud_rate: float) -> None:
    """
    Update current fraud rate gauge.

    Args:
        fraud_rate: Fraud rate percentage (0-100)
    """
    try:
        FRAUD_RATE.set(fraud_rate)

        logger.debug("Fraud rate updated", extra={"fraud_rate": fraud_rate})
    except Exception as e:
        logger.error(f"Error updating fraud rate: {e}")
