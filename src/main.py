from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import logging

from src.api.v1.router import api_router
from src.api.v1.endpoints.metrics import router as metrics_router
from src.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuthMiddleware
)
from src.middleware.metrics_middleware import MetricsMiddleware
from src.core.config import settings
from src.core.metrics import set_model_info
from src.dependencies import get_prisma, get_redis_client

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time fraud detection API for e-commerce and fintech",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENABLE_SWAGGER else None,
    redoc_url="/redoc" if settings.ENABLE_SWAGGER else None,
)

# CORS - Using centralized configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

# Metrics middleware - FIRST to track all requests (Day 7)
app.add_middleware(MetricsMiddleware)

# Security middlewares (order matters: SecurityHeaders -> RateLimit -> Auth)
# SecurityHeadersMiddleware adds security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)

# RateLimitMiddleware enforces rate limits per API key
app.add_middleware(RateLimitMiddleware)

# AuthMiddleware validates API keys on all requests
app.add_middleware(AuthMiddleware)


@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    Day 7: Set ML model info for Prometheus metrics.
    """
    logger.info("Application starting up")

    # Initialize ML model info metric (Day 7) - Make this optional to prevent startup delays
    try:
        # Check if required ML config exists before attempting to load
        if not hasattr(settings, 'ML_MODEL_PATH') or not hasattr(settings, 'ML_MODEL_VERSION'):
            logger.warning("ML model configuration not found, skipping ML initialization")
            return

        from src.ml.model_manager import ModelManager

        # Instantiate and load model with timeout protection
        manager = ModelManager()
        model_loaded = manager.load_model()
        
        if model_loaded:
            # Get model info
            model_info = manager.get_model_info()
            model_version = settings.ML_MODEL_VERSION
            model_type = "xgboost"

            set_model_info(model_version, model_type)

            logger.info(
                "ML model info initialized",
                extra={
                    "model_version": model_version,
                    "model_type": model_type,
                    "model_loaded": model_info.get('model_loaded', False)
                }
            )
        else:
            logger.warning("ML model could not be loaded, continuing without ML metrics")
    except ImportError as e:
        logger.warning(f"ML dependencies not available: {e}")
    except Exception as e:
        logger.warning(f"Could not initialize ML model info: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """
    Basic health check - fast, no dependencies.
    Use for load balancer liveness probe.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies.
    Use for load balancer readiness probe.

    Checks:
    - Database connection (Prisma)
    - Redis connection
    """
    start_time = time.time()
    checks = {}
    overall_healthy = True

    # Check Database (Prisma)
    try:
        prisma = await get_prisma()
        # Simple query to verify connection
        await prisma.execute_raw("SELECT 1")
        db_latency = int((time.time() - start_time) * 1000)
        checks["database"] = {
            "status": "healthy",
            "latency_ms": db_latency
        }
        logger.debug(f"Database health check passed: {db_latency}ms")
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
        logger.error(f"Database health check failed: {str(e)}")

    # Check Redis
    try:
        redis_start = time.time()
        redis = get_redis_client()
        redis.ping()
        redis_latency = int((time.time() - redis_start) * 1000)
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": redis_latency
        }
        logger.debug(f"Redis health check passed: {redis_latency}ms")
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
        logger.error(f"Redis health check failed: {str(e)}")

    # Calculate total duration
    duration_ms = int((time.time() - start_time) * 1000)

    response_data = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
        "duration_ms": duration_ms
    }

    if overall_healthy:
        logger.info(f"Readiness check passed in {duration_ms}ms")
        return response_data
    else:
        logger.warning(f"Readiness check failed in {duration_ms}ms", extra=response_data)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data
        )


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENABLE_SWAGGER else None
    }


# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(metrics_router)  # Prometheus metrics at /metrics (Day 7)
