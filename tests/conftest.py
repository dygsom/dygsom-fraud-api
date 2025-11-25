"""
Test fixtures and configuration.
Provides reusable test fixtures for API testing.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from httpx import AsyncClient
from prisma import Prisma

from src.main import app
from src.core.security import SecurityUtils
from src.repositories.api_key_repository import ApiKeyRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def prisma_client() -> AsyncGenerator[Prisma, None]:
    """Prisma client for tests"""
    prisma = Prisma()
    await prisma.connect()
    yield prisma
    await prisma.disconnect()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_api_key(prisma_client: Prisma) -> dict:
    """Create test API key with 100 req/min limit
    
    Returns:
        dict with 'plain_key', 'hashed_key', and 'key_data'
    """
    # Generate API key
    plain_key, key_hash = SecurityUtils.generate_and_hash()
    
    # Create repository
    api_key_repo = ApiKeyRepository(prisma_client)
    
    # Create API key in database
    key_data = await api_key_repo.create_api_key(
        key_hash=key_hash,
        name="Test API Key",
        description="API key for testing",
        rate_limit=100,
        expires_at=datetime.utcnow() + timedelta(days=1),
        created_by="pytest"
    )
    
    return {
        "plain_key": plain_key,
        "hashed_key": key_hash,
        "key_data": key_data
    }


@pytest_asyncio.fixture
async def test_api_key_low_limit(prisma_client: Prisma) -> dict:
    """Create test API key with LOW rate limit (5 req/min) for rate limit testing
    
    Returns:
        dict with 'plain_key', 'hashed_key', and 'key_data'
    """
    # Generate API key
    plain_key, key_hash = SecurityUtils.generate_and_hash()
    
    # Create repository
    api_key_repo = ApiKeyRepository(prisma_client)
    
    # Create API key in database
    key_data = await api_key_repo.create_api_key(
        key_hash=key_hash,
        name="Test API Key (Low Limit)",
        description="API key for rate limit testing",
        rate_limit=5,  # Very low limit
        expires_at=datetime.utcnow() + timedelta(days=1),
        created_by="pytest"
    )
    
    return {
        "plain_key": plain_key,
        "hashed_key": key_hash,
        "key_data": key_data
    }


@pytest_asyncio.fixture
async def expired_api_key(prisma_client: Prisma) -> dict:
    """Create EXPIRED test API key
    
    Returns:
        dict with 'plain_key', 'hashed_key', and 'key_data'
    """
    # Generate API key
    plain_key, key_hash = SecurityUtils.generate_and_hash()
    
    # Create repository
    api_key_repo = ApiKeyRepository(prisma_client)
    
    # Create API key with past expiration
    key_data = await api_key_repo.create_api_key(
        key_hash=key_hash,
        name="Expired Test API Key",
        description="Expired API key for testing",
        rate_limit=100,
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
        created_by="pytest"
    )
    
    return {
        "plain_key": plain_key,
        "hashed_key": key_hash,
        "key_data": key_data
    }


@pytest.fixture
def auth_headers(test_api_key: dict) -> dict:
    """Headers with valid API key
    
    Args:
        test_api_key: Test API key fixture
        
    Returns:
        dict with X-API-Key header
    """
    return {
        "X-API-Key": test_api_key["plain_key"]
    }


@pytest.fixture
def sample_transaction_data() -> dict:
    """Sample transaction data for fraud detection
    
    Returns:
        dict with transaction fields
    """
    return {
        "user_id": "user123",
        "amount": 150.00,
        "currency": "USD",
        "merchant_id": "merchant456",
        "merchant_category": "retail",
        "country": "US",
        "device_id": "device789",
        "ip_address": "192.168.1.1",
        "transaction_type": "purchase"
    }
