"""
API Router V1
Main router for API version 1
"""

from fastapi import APIRouter

# Create main router
api_router = APIRouter()

# Import endpoint routers
from src.api.v1.endpoints import fraud, admin

# Include sub-routers
api_router.include_router(fraud.router, tags=["Fraud Detection"])
api_router.include_router(admin.router, tags=["Admin - API Keys"])
