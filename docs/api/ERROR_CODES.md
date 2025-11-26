# Error Codes Reference

**Version:** 1.0.0
**Last Updated:** 2025-01-25

This document provides a comprehensive reference for all error codes returned by the DYGSOM Fraud Detection API.

## Table of Contents

- [Error Response Format](#error-response-format)
- [HTTP Status Codes](#http-status-codes)
- [Error Code Reference](#error-code-reference)
- [Handling Specific Errors](#handling-specific-errors)
- [Rate Limiting](#rate-limiting)
- [Best Practices](#best-practices)

---

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error description",
    "details": {
      "field": "additional_context"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error.code` | string | Machine-readable error code |
| `error.message` | string | Human-readable error message |
| `error.details` | object | Additional error context (optional) |
| `timestamp` | string | ISO 8601 UTC timestamp of error |

---

## HTTP Status Codes

| Status Code | Category | Description |
|-------------|----------|-------------|
| **2xx** | Success | Request succeeded |
| **4xx** | Client Error | Invalid request from client |
| **5xx** | Server Error | Error on API server side |

---

## Error Code Reference

### 400 Bad Request

#### invalid_request

**Description:** The request body is malformed or cannot be parsed.

**Common Causes:**
- Invalid JSON syntax
- Missing request body
- Wrong Content-Type header

**Example Response:**
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

**Resolution:**
- Verify JSON syntax is valid
- Include `Content-Type: application/json` header
- Ensure request body is not empty

**Example Fix:**
```bash
# Incorrect - missing quotes
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -d '{amount: 100}'

# Correct - valid JSON
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'
```

---

### 401 Unauthorized

#### unauthorized

**Description:** API key is missing or invalid.

**Common Causes:**
- Missing `X-API-Key` header
- Invalid API key format
- Expired or revoked API key

**Example Response:**
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

**Resolution:**
- Include `X-API-Key` header in request
- Verify API key is correct
- Generate new API key if expired

**Example Fix:**
```bash
# Incorrect - missing API key header
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -d '{"transaction_id": "tx-001"}'

# Correct - includes API key
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -H "X-API-Key: dygsom_your_api_key_here" \
  -d '{"transaction_id": "tx-001"}'
```

---

### 403 Forbidden

#### forbidden

**Description:** API key is valid but inactive or suspended.

**Common Causes:**
- Account suspended due to payment issues
- API key explicitly disabled
- Account exceeds usage limits

**Example Response:**
```json
{
  "error": {
    "code": "forbidden",
    "message": "API key is inactive or suspended",
    "details": {
      "reason": "account_suspended",
      "contact": "support@dygsom.com"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

**Resolution:**
- Contact support@dygsom.com
- Check account status in dashboard
- Verify payment information

---

### 422 Unprocessable Entity

#### validation_error

**Description:** One or more fields failed validation.

**Common Causes:**
- Invalid email format
- Missing required fields
- Invalid data types
- Values out of acceptable range

**Example Response:**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Field validation failed",
    "details": {
      "field": "customer_email",
      "error": "Invalid email format",
      "value": "invalid-email"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

**Validation Rules:**

| Field | Rules |
|-------|-------|
| `transaction_id` | Required, string, max 100 characters |
| `customer_email` | Required, valid email format |
| `customer_ip` | Required, valid IPv4 or IPv6 address |
| `amount` | Required, positive number |
| `currency` | Required, ISO 4217 code (USD, EUR, etc.) |
| `merchant_id` | Required, string, max 100 characters |
| `card_bin` | Required, 6-digit numeric string |
| `device_id` | Required, string, max 100 characters |
| `timestamp` | Required, ISO 8601 UTC timestamp |

**Resolution:**
- Check field formats match validation rules
- Ensure all required fields are present
- Validate data types (string, number, etc.)

**Example Fix:**
```python
# Incorrect - invalid email
transaction = {
    "customer_email": "not-an-email"
}

# Correct - valid email
transaction = {
    "customer_email": "user@example.com"
}
```

---

### 429 Too Many Requests

#### rate_limit_exceeded

**Description:** Request rate limit has been exceeded.

**Common Causes:**
- Too many requests in short time window
- Burst limit exceeded
- Sustained high request rate

**Example Response:**
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

**Rate Limits by Tier:**

| Tier | Requests/Minute | Burst Allowance |
|------|----------------|-----------------|
| Startup | 100 | 20 |
| Growth | 500 | 100 |
| Enterprise | 2000 | 500 |

**Resolution:**
- Implement exponential backoff retry logic
- Respect `Retry-After` header value
- Consider upgrading tier if consistently hitting limits
- Distribute requests more evenly over time

**Example Fix:**
```python
import time

def call_api_with_backoff(transaction, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.check_fraud(transaction)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                retry_after = e.retry_after
                wait_time = min(retry_after * (2 ** attempt), 300)
                time.sleep(wait_time)
                continue
            raise
```

---

### 500 Internal Server Error

#### internal_error

**Description:** Unexpected error occurred on the server.

**Common Causes:**
- Temporary server issue
- Database connection problem
- ML model error

**Example Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected error occurred",
    "details": {
      "request_id": "req_abc123def456"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

**Resolution:**
- Retry the request (with exponential backoff)
- If error persists, contact support
- Include `request_id` from error details

---

### 503 Service Unavailable

#### service_unavailable

**Description:** API is temporarily unavailable.

**Common Causes:**
- Scheduled maintenance
- High load / overload condition
- Dependency (database, cache) unavailable

**Example Response:**
```json
{
  "error": {
    "code": "service_unavailable",
    "message": "Service is temporarily unavailable",
    "details": {
      "retry_after": 60,
      "status_page": "https://status.dygsom.com"
    }
  },
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

**Resolution:**
- Retry with exponential backoff
- Check status page for maintenance notifications
- Implement fallback to safe default (REVIEW)

---

## Handling Specific Errors

### Authentication Errors (401, 403)

**Do NOT retry** - These are permanent errors that won't be resolved by retrying.

```python
def handle_auth_error(error):
    logger.error(f"Authentication failed: {error.message}")
    # Alert operations team
    send_alert("API authentication failure")
    # Do not retry
    raise
```

### Validation Errors (422)

**Do NOT retry** - Fix the request data before retrying.

```python
def handle_validation_error(error):
    logger.error(f"Validation failed: {error.details}")
    # Log the problematic request
    # Fix data and retry with corrected data
    raise
```

### Rate Limit Errors (429)

**DO retry** - After waiting for the specified time.

```python
def handle_rate_limit(error):
    retry_after = error.details.get('retry_after', 60)
    logger.warning(f"Rate limit hit, retrying after {retry_after}s")
    time.sleep(retry_after)
    # Retry request
```

### Server Errors (500, 503)

**DO retry** - With exponential backoff.

```python
def handle_server_error(error, attempt):
    wait_time = min(2 ** attempt, 60)
    logger.warning(f"Server error, retrying after {wait_time}s")
    time.sleep(wait_time)
    # Retry request
```

---

## Rate Limiting

### Rate Limit Headers

Every response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1737804660
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in current window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

### Monitoring Rate Limits

```python
def check_rate_limit_status(response):
    limit = int(response.headers.get('X-RateLimit-Limit', 0))
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset = int(response.headers.get('X-RateLimit-Reset', 0))

    usage_percent = ((limit - remaining) / limit) * 100

    if usage_percent > 80:
        logger.warning(f"Rate limit usage at {usage_percent}%")

    return {
        'limit': limit,
        'remaining': remaining,
        'reset': reset,
        'usage_percent': usage_percent
    }
```

---

## Best Practices

### 1. Implement Comprehensive Error Handling

Handle all possible error codes explicitly:

```python
try:
    result = client.check_fraud(transaction)
except AuthenticationError:
    # Handle 401/403
except ValidationError:
    # Handle 422
except RateLimitError:
    # Handle 429
except ServerError:
    # Handle 500/503
except Exception:
    # Handle unexpected errors
```

### 2. Use Exponential Backoff for Retries

```python
def exponential_backoff(attempt, max_wait=60):
    return min(2 ** attempt, max_wait)
```

### 3. Log All Errors with Context

```python
logger.error(
    f"API error: {error.code}",
    extra={
        'transaction_id': transaction['transaction_id'],
        'status_code': error.status_code,
        'error_details': error.details
    }
)
```

### 4. Monitor Error Rates

Set up alerts for:
- Error rate > 1%
- Rate limit errors > 10/minute
- Authentication errors > 0

### 5. Implement Circuit Breaker

Prevent cascading failures by implementing circuit breaker pattern for persistent errors.

---

## Support

If you encounter errors not documented here or need assistance:

**Email:** support@dygsom.com
**Status Page:** https://status.dygsom.com
**Documentation:** https://docs.dygsom.com

When reporting errors, include:
- Error code and message
- Request ID (from error details)
- Timestamp of error
- Steps to reproduce

---

**Last Updated:** 2025-01-25
**Version:** 1.0.0
