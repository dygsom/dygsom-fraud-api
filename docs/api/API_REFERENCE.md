# API Reference

**Version:** 1.0.0
**Base URL:** `https://api.dygsom.pe`
**Last Updated:** 2025-01-25

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [POST /api/v1/fraud/score](#post-apiv1fraudscore)
  - [GET /health](#get-health)
  - [GET /health/ready](#get-healthready)
- [Data Models](#data-models)
- [Risk Levels](#risk-levels)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)
- [Best Practices](#best-practices)

---

## Authentication

All API requests require authentication via an API key passed in the request header.

**Header Name:** `X-API-Key`
**Format:** `dygsom_<32_character_token>`

### Example

```http
POST /api/v1/fraud/score HTTP/1.1
Host: api.dygsom.pe
Content-Type: application/json
X-API-Key: dygsom_abc123def456ghi789jkl012mno345pq
```

### Obtaining an API Key

1. Sign up at [https://dygsom.pe/signup](https://dygsom.pe/signup)
2. Navigate to Dashboard > API Keys
3. Generate a new API key
4. Store the key securely (it will only be shown once)

**Security Note:** Never commit API keys to version control or expose them in client-side code.

---

## Endpoints

### POST /api/v1/fraud/score

Evaluate a transaction for fraud risk and receive a real-time risk assessment.

**URL:** `/api/v1/fraud/score`
**Method:** `POST`
**Content-Type:** `application/json`
**Authentication:** Required

#### Request Body

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `transaction_id` | string | Yes | Unique identifier for the transaction | `"tx-123456789"` |
| `customer_email` | string | Yes | Customer's email address | `"user@example.com"` |
| `customer_ip` | string | Yes | Customer's IP address (IPv4 or IPv6) | `"192.168.1.1"` |
| `amount` | number | Yes | Transaction amount (decimal) | `150.50` |
| `currency` | string | Yes | ISO 4217 currency code | `"USD"`, `"EUR"`, `"PEN"` |
| `merchant_id` | string | Yes | Merchant identifier | `"merchant-001"` |
| `card_bin` | string | Yes | First 6 digits of card number | `"424242"` |
| `device_id` | string | Yes | Device fingerprint or identifier | `"device-abc123"` |
| `timestamp` | string | Yes | ISO 8601 formatted timestamp (UTC) | `"2025-01-25T10:30:00Z"` |

#### Request Example

```json
{
  "transaction_id": "tx-1737804600000-A1B2C3",
  "customer_email": "john.doe@example.com",
  "customer_ip": "203.0.113.45",
  "amount": 299.99,
  "currency": "USD",
  "merchant_id": "merchant-042",
  "card_bin": "424242",
  "device_id": "device-xyz789",
  "timestamp": "2025-01-25T10:30:00Z"
}
```

#### Response (Success - 200 OK)

| Field | Type | Description |
|-------|------|-------------|
| `fraud_score` | number | Fraud probability (0.0 to 1.0) |
| `risk_level` | string | Risk category: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `recommendation` | string | Action recommendation: `APPROVE`, `REVIEW`, `REJECT` |
| `factors` | object | Contributing risk factors |
| `factors.velocity_score` | number | Transaction velocity risk (0.0 to 1.0) |
| `factors.amount_risk` | number | Amount-based risk (0.0 to 1.0) |
| `factors.location_risk` | number | Location-based risk (0.0 to 1.0) |
| `factors.device_risk` | number | Device-based risk (0.0 to 1.0) |
| `processing_time_ms` | number | API processing time in milliseconds |
| `timestamp` | string | Response timestamp (ISO 8601 UTC) |

#### Response Example

```json
{
  "fraud_score": 0.23,
  "risk_level": "LOW",
  "recommendation": "APPROVE",
  "factors": {
    "velocity_score": 0.15,
    "amount_risk": 0.20,
    "location_risk": 0.10,
    "device_risk": 0.18
  },
  "processing_time_ms": 45,
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### cURL Example

```bash
curl -X POST https://api.dygsom.pe/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dygsom_your_api_key_here" \
  -d '{
    "transaction_id": "tx-1737804600000-A1B2C3",
    "customer_email": "john.doe@example.com",
    "customer_ip": "203.0.113.45",
    "amount": 299.99,
    "currency": "USD",
    "merchant_id": "merchant-042",
    "card_bin": "424242",
    "device_id": "device-xyz789",
    "timestamp": "2025-01-25T10:30:00Z"
  }'
```

---

### GET /health

Basic health check endpoint to verify API availability.

**URL:** `/health`
**Method:** `GET`
**Authentication:** Not required

#### Response (Success - 200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### cURL Example

```bash
curl -X GET https://api.dygsom.pe/health
```

---

### GET /health/ready

Comprehensive readiness check that validates all dependencies (database, cache, ML model).

**URL:** `/health/ready`
**Method:** `GET`
**Authentication:** Not required

#### Response (Success - 200 OK)

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "ml_model": "ok"
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### Response (Service Unavailable - 503)

```json
{
  "status": "not_ready",
  "checks": {
    "database": "ok",
    "cache": "error",
    "ml_model": "ok"
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### cURL Example

```bash
curl -X GET https://api.dygsom.pe/health/ready
```

---

## Data Models

### Transaction Object

Used in fraud scoring requests.

```typescript
interface Transaction {
  transaction_id: string;    // Unique transaction identifier
  customer_email: string;    // Valid email format
  customer_ip: string;       // IPv4 or IPv6 address
  amount: number;            // Positive decimal number
  currency: string;          // ISO 4217 code (3 characters)
  merchant_id: string;       // Merchant identifier
  card_bin: string;          // 6-digit numeric string
  device_id: string;         // Device identifier
  timestamp: string;         // ISO 8601 UTC timestamp
}
```

### Fraud Assessment Object

Returned by fraud scoring endpoint.

```typescript
interface FraudAssessment {
  fraud_score: number;       // Range: 0.0 - 1.0
  risk_level: RiskLevel;     // LOW | MEDIUM | HIGH | CRITICAL
  recommendation: Action;    // APPROVE | REVIEW | REJECT
  factors: RiskFactors;
  processing_time_ms: number;
  timestamp: string;
}

interface RiskFactors {
  velocity_score: number;    // Range: 0.0 - 1.0
  amount_risk: number;       // Range: 0.0 - 1.0
  location_risk: number;     // Range: 0.0 - 1.0
  device_risk: number;       // Range: 0.0 - 1.0
}
```

---

## Risk Levels

The API categorizes transactions into four risk levels based on the fraud score.

| Risk Level | Fraud Score Range | Description | Recommendation |
|------------|-------------------|-------------|----------------|
| **LOW** | 0.0 - 0.3 | Minimal fraud indicators detected | APPROVE - Process transaction normally |
| **MEDIUM** | 0.3 - 0.5 | Some fraud indicators present | REVIEW - Manual review recommended |
| **HIGH** | 0.5 - 0.8 | Multiple fraud indicators detected | REVIEW - Thorough review required |
| **CRITICAL** | 0.8 - 1.0 | Strong fraud indicators present | REJECT - Block transaction |

### Recommendation Actions

| Action | Description | Suggested Implementation |
|--------|-------------|-------------------------|
| **APPROVE** | Low risk - proceed with transaction | Complete payment processing |
| **REVIEW** | Medium/High risk - requires human review | Hold transaction, flag for manual review |
| **REJECT** | Critical risk - block transaction | Decline transaction, notify customer |

---

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error description",
    "details": {}
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

### HTTP Status Codes

| Status Code | Error Code | Description | Resolution |
|-------------|------------|-------------|------------|
| **400** | `invalid_request` | Request body is malformed or missing required fields | Verify request format and required fields |
| **401** | `unauthorized` | Missing or invalid API key | Include valid X-API-Key header |
| **403** | `forbidden` | API key is inactive or suspended | Contact support to reactivate key |
| **422** | `validation_error` | One or more fields failed validation | Check field formats and constraints |
| **429** | `rate_limit_exceeded` | Request rate limit exceeded | Retry after 60 seconds |
| **500** | `internal_error` | Unexpected server error | Retry request or contact support |
| **503** | `service_unavailable` | Service temporarily unavailable | Retry with exponential backoff |

### Error Examples

#### 400 Bad Request

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request body is malformed",
    "details": {
      "error": "Expecting value: line 1 column 1 (char 0)"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### 401 Unauthorized

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Missing or invalid API key",
    "details": {
      "header": "X-API-Key header is required"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### 422 Validation Error

```json
{
  "error": {
    "code": "validation_error",
    "message": "Field validation failed",
    "details": {
      "field": "customer_email",
      "error": "Invalid email format"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

#### 429 Rate Limit Exceeded

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Request rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": "60s",
      "retry_after": 42
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

---

## Rate Limiting

Rate limits are applied per API key to ensure fair usage and system stability.

### Limits

| Tier | Requests per Minute | Burst Allowance |
|------|---------------------|-----------------|
| **Startup** | 100 | 20 |
| **Growth** | 500 | 100 |
| **Enterprise** | 2000 | 500 |

### Rate Limit Headers

Every API response includes rate limit information in headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1737804660
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per minute |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

### Handling Rate Limits

When rate limit is exceeded (HTTP 429), implement exponential backoff:

```python
import time

def call_api_with_backoff(transaction, max_retries=3):
    for attempt in range(max_retries):
        response = call_fraud_api(transaction)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            wait_time = min(retry_after * (2 ** attempt), 300)
            time.sleep(wait_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

---

## Best Practices

### 1. Always Use HTTPS

Never send API requests over unencrypted HTTP. Always use `https://` URLs to protect sensitive transaction data.

```python
# Correct
API_URL = "https://api.dygsom.pe/api/v1/fraud/score"

# Incorrect - Never use HTTP
API_URL = "http://api.dygsom.pe/api/v1/fraud/score"
```

### 2. Store API Keys Securely

Never hardcode API keys in source code. Use environment variables or secure credential management systems.

```python
import os

# Correct - Environment variable
API_KEY = os.getenv("DYGSOM_API_KEY")

# Incorrect - Hardcoded key
API_KEY = "dygsom_abc123def456"  # Never do this
```

### 3. Implement Timeout Handling

Set reasonable timeouts to prevent indefinite waiting.

```python
import requests

response = requests.post(
    API_URL,
    json=transaction,
    headers={"X-API-Key": API_KEY},
    timeout=5  # 5 second timeout
)
```

### 4. Use Unique Transaction IDs

Generate globally unique transaction IDs to enable proper tracking and avoid duplicate processing.

```python
import uuid
import time

def generate_transaction_id():
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"tx-{timestamp}-{unique_id}"
```

### 5. Include Accurate Timestamps

Always use UTC timestamps in ISO 8601 format for consistency.

```python
from datetime import datetime

timestamp = datetime.utcnow().isoformat() + "Z"
# Result: "2025-01-25T10:30:00.123456Z"
```

### 6. Implement Retry Logic

Handle transient failures with exponential backoff retry logic.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_fraud_api(transaction):
    response = requests.post(API_URL, json=transaction, headers=headers)
    response.raise_for_status()
    return response.json()
```

### 7. Log All API Interactions

Maintain comprehensive logs for debugging and audit trails.

```python
import logging

logger = logging.getLogger(__name__)

def check_fraud(transaction):
    logger.info(f"Checking fraud for transaction {transaction['transaction_id']}")

    try:
        response = call_fraud_api(transaction)
        logger.info(f"Fraud check complete: {response['risk_level']}")
        return response
    except Exception as e:
        logger.error(f"Fraud check failed: {str(e)}")
        raise
```

### 8. Cache Results Appropriately

Cache fraud assessment results for a short period (5 minutes) to reduce API calls for duplicate checks.

```python
from functools import lru_cache
import hashlib
import json

@lru_cache(maxsize=1000)
def get_cached_fraud_score(transaction_json):
    transaction = json.loads(transaction_json)
    return call_fraud_api(transaction)

def check_fraud_cached(transaction):
    # Use transaction as cache key
    cache_key = json.dumps(transaction, sort_keys=True)
    return get_cached_fraud_score(cache_key)
```

### 9. Handle All Response Codes

Implement proper handling for all possible HTTP response codes.

```python
def process_fraud_response(response):
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise AuthenticationError("Invalid API key")
    elif response.status_code == 422:
        raise ValidationError("Invalid transaction data")
    elif response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif response.status_code >= 500:
        raise ServerError("API server error")
    else:
        raise APIError(f"Unexpected status code: {response.status_code}")
```

### 10. Monitor API Performance

Track API response times and error rates to detect issues early.

```python
import time
from prometheus_client import Counter, Histogram

api_calls = Counter('fraud_api_calls_total', 'Total fraud API calls')
api_errors = Counter('fraud_api_errors_total', 'Total fraud API errors')
api_latency = Histogram('fraud_api_latency_seconds', 'Fraud API latency')

def check_fraud_monitored(transaction):
    api_calls.inc()

    start = time.time()
    try:
        response = call_fraud_api(transaction)
        return response
    except Exception as e:
        api_errors.inc()
        raise
    finally:
        api_latency.observe(time.time() - start)
```

---

## Support

For technical support or questions about the API:

- **Email:** support@dygsom.pe
- **Documentation:** https://docs.dygsom.pe
- **Status Page:** https://status.dygsom.pe
- **Community Slack:** https://slack.dygsom.pe

For urgent issues affecting production systems, please include "[URGENT]" in the email subject line.

---

**Last Updated:** 2025-01-25
**API Version:** 1.0.0
**Document Version:** 1.0.0
