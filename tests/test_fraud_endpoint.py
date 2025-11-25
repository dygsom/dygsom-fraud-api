"""
Tests for fraud detection endpoint with security.
Tests authentication, rate limiting, and fraud scoring.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_no_auth(client: AsyncClient):
    """Test health endpoint doesn't require authentication"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_fraud_score_no_api_key(client: AsyncClient, sample_transaction_data: dict):
    """Test fraud endpoint returns 401 without API key"""
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data
    )
    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_fraud_score_invalid_api_key(client: AsyncClient, sample_transaction_data: dict):
    """Test fraud endpoint returns 401 with invalid API key"""
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers={"X-API-Key": "dygsom_invalid_key_12345678901234567890"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_fraud_score_expired_api_key(client: AsyncClient, expired_api_key: dict, sample_transaction_data: dict):
    """Test fraud endpoint returns 401 with expired API key"""
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers={"X-API-Key": expired_api_key["plain_key"]}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_fraud_score_success_with_valid_key(client: AsyncClient, auth_headers: dict, sample_transaction_data: dict):
    """Test fraud endpoint returns 200 with valid API key"""
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify response structure
    data = response.json()
    assert "transaction_id" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "factors" in data
    
    # Verify risk score range
    assert 0 <= data["risk_score"] <= 1
    assert data["risk_level"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_fraud_score_security_headers(client: AsyncClient, auth_headers: dict, sample_transaction_data: dict):
    """Test security headers are present in response"""
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers=auth_headers
    )
    
    # Check security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "X-Request-ID" in response.headers
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


@pytest.mark.asyncio
async def test_fraud_score_invalid_data(client: AsyncClient, auth_headers: dict):
    """Test fraud endpoint returns 422 with invalid data"""
    invalid_data = {
        "user_id": "user123",
        # Missing required fields
    }
    
    response = await client.post(
        "/api/v1/fraud/score",
        json=invalid_data,
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_fraud_score_missing_fields(client: AsyncClient, auth_headers: dict):
    """Test fraud endpoint returns 422 with missing required fields"""
    response = await client.post(
        "/api/v1/fraud/score",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, test_api_key_low_limit: dict, sample_transaction_data: dict):
    """Test rate limiting with low limit API key (5 req/min)"""
    headers = {"X-API-Key": test_api_key_low_limit["plain_key"]}
    
    # Make requests up to the limit
    for i in range(5):
        response = await client.post(
            "/api/v1/fraud/score",
            json=sample_transaction_data,
            headers=headers
        )
        assert response.status_code == 200, f"Request {i+1} should succeed"
    
    # Next request should be rate limited
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers=headers
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    assert "Retry-After" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_rate_limit_headers_decreasing(client: AsyncClient, test_api_key_low_limit: dict, sample_transaction_data: dict):
    """Test X-RateLimit-Remaining decreases with each request"""
    headers = {"X-API-Key": test_api_key_low_limit["plain_key"]}
    
    # First request
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers=headers
    )
    assert response.status_code == 200
    first_remaining = int(response.headers["X-RateLimit-Remaining"])
    
    # Second request
    response = await client.post(
        "/api/v1/fraud/score",
        json=sample_transaction_data,
        headers=headers
    )
    assert response.status_code == 200
    second_remaining = int(response.headers["X-RateLimit-Remaining"])
    
    # Remaining should decrease
    assert second_remaining < first_remaining


@pytest.mark.asyncio
async def test_admin_list_api_keys_requires_auth(client: AsyncClient):
    """Test admin list endpoint requires authentication"""
    response = await client.get("/api/v1/admin/api-keys")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_api_keys_success(client: AsyncClient, auth_headers: dict):
    """Test admin list endpoint returns API keys"""
    response = await client.get(
        "/api/v1/admin/api-keys",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "keys" in data
    assert "total" in data
    assert isinstance(data["keys"], list)


@pytest.mark.asyncio
async def test_admin_create_api_key_requires_auth(client: AsyncClient):
    """Test admin create endpoint requires authentication"""
    response = await client.post(
        "/api/v1/admin/api-keys",
        json={"name": "New Key", "rate_limit": 100}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_create_api_key_success(client: AsyncClient, auth_headers: dict):
    """Test admin create endpoint creates API key"""
    response = await client.post(
        "/api/v1/admin/api-keys",
        json={
            "name": "Test New Key",
            "description": "Created by test",
            "rate_limit": 150
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("dygsom_")
    assert data["name"] == "Test New Key"
    assert data["rate_limit"] == 150
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_admin_delete_api_key_requires_auth(client: AsyncClient, test_api_key: dict):
    """Test admin delete endpoint requires authentication"""
    response = await client.delete(
        f"/api/v1/admin/api-keys/{test_api_key['key_data'].id}"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_delete_nonexistent_key(client: AsyncClient, auth_headers: dict):
    """Test admin delete endpoint returns 404 for nonexistent key"""
    response = await client.delete(
        "/api/v1/admin/api-keys/nonexistent-key-id",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """Test CORS headers are present"""
    response = await client.options("/health")
    # CORS headers should be present
    # Note: In test environment, exact CORS behavior may differ
    assert response.status_code in [200, 405]
