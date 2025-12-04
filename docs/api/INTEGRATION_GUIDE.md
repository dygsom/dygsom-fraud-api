# Integration Guide

**Version:** 1.0.0
**Estimated Time:** 30-60 minutes
**Prerequisites:** API key, development environment
**Last Updated:** 2025-01-25

This guide walks you through integrating the DYGSOM Fraud Detection API into your application in seven steps.

## Table of Contents

1. [Get API Credentials](#step-1-get-api-credentials)
2. [Make Your First API Call](#step-2-make-your-first-api-call)
3. [Integrate Into Your Application](#step-3-integrate-into-your-application)
4. [Handle Responses](#step-4-handle-responses)
5. [Implement Error Handling](#step-5-implement-error-handling)
6. [Test Your Integration](#step-6-test-your-integration)
7. [Go Live](#step-7-go-live)

---

## Step 1: Get API Credentials

### 1.1 Create an Account

1. Visit [https://dygsom.pe/signup](https://dygsom.pe/signup)
2. Complete the registration form
3. Verify your email address
4. Log in to your dashboard

### 1.2 Generate API Key

1. Navigate to **Dashboard > API Keys**
2. Click **Generate New Key**
3. Enter a descriptive name (e.g., "Production", "Staging")
4. Copy the API key immediately (it will only be shown once)
5. Store it securely in your password manager or secrets management system

**API Key Format:**
```
dygsom_abc123def456ghi789jkl012mno345pq
```

### 1.3 Store API Key Securely

**Environment Variable (Recommended):**
```bash
# .env file
DYGSOM_API_KEY=dygsom_your_api_key_here
```

**Never commit API keys to version control**. Add `.env` to your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

---

## Step 2: Make Your First API Call

Test the API using cURL to verify your credentials and understand the response format.

### 2.1 Health Check

Verify API availability:

```bash
curl -X GET https://api.dygsom.pe/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

### 2.2 Fraud Score Request

Make your first fraud assessment:

```bash
curl -X POST https://api.dygsom.pe/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dygsom_your_api_key_here" \
  -d '{
    "transaction_id": "test-tx-001",
    "customer_email": "test@example.com",
    "customer_ip": "203.0.113.45",
    "amount": 99.99,
    "currency": "USD",
    "merchant_id": "merchant-test",
    "card_bin": "424242",
    "device_id": "device-test-001",
    "timestamp": "2025-01-25T10:30:00Z"
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 0.15,
  "risk_level": "LOW",
  "recommendation": "APPROVE",
  "factors": {
    "velocity_score": 0.10,
    "amount_risk": 0.12,
    "location_risk": 0.08,
    "device_risk": 0.20
  },
  "processing_time_ms": 45,
  "timestamp": "2025-01-25T10:30:00.123Z"
}
```

If you receive this response, your API key is working correctly.

---

## Step 3: Integrate Into Your Application

Choose your programming language and follow the integration example.

### 3.1 Python Integration

**Install Dependencies:**
```bash
pip install requests python-dotenv
```

**Implementation:**
```python
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DYGSOMFraudClient:
    """Client for DYGSOM Fraud Detection API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DYGSOM_API_KEY")
        self.base_url = "https://api.dygsom.pe"
        self.timeout = 5  # seconds

        if not self.api_key:
            raise ValueError("API key is required")

    def check_fraud(self, transaction):
        """
        Check a transaction for fraud.

        Args:
            transaction (dict): Transaction data

        Returns:
            dict: Fraud assessment result

        Raises:
            requests.HTTPError: On API error
        """
        url = f"{self.base_url}/api/v1/fraud/score"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

        try:
            response = requests.post(
                url,
                json=transaction,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            raise Exception("API request timed out")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception("Rate limit exceeded")
            raise


# Usage Example
if __name__ == "__main__":
    client = DYGSOMFraudClient()

    transaction = {
        "transaction_id": "tx-1737804600000-TEST",
        "customer_email": "john.doe@example.com",
        "customer_ip": "203.0.113.45",
        "amount": 299.99,
        "currency": "USD",
        "merchant_id": "merchant-042",
        "card_bin": "424242",
        "device_id": "device-xyz789",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    result = client.check_fraud(transaction)

    print(f"Fraud Score: {result['fraud_score']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Recommendation: {result['recommendation']}")
```

### 3.2 Node.js Integration

**Install Dependencies:**
```bash
npm install axios dotenv
```

**Implementation:**
```javascript
const axios = require('axios');
require('dotenv').config();

class DYGSOMFraudClient {
  constructor(apiKey = null) {
    this.apiKey = apiKey || process.env.DYGSOM_API_KEY;
    this.baseURL = 'https://api.dygsom.pe';
    this.timeout = 5000; // milliseconds

    if (!this.apiKey) {
      throw new Error('API key is required');
    }

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      }
    });
  }

  async checkFraud(transaction) {
    try {
      const response = await this.client.post(
        '/api/v1/fraud/score',
        transaction
      );
      return response.data;

    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        throw new Error('API request timed out');
      }
      if (error.response?.status === 429) {
        throw new Error('Rate limit exceeded');
      }
      throw error;
    }
  }
}

// Usage Example
async function main() {
  const client = new DYGSOMFraudClient();

  const transaction = {
    transaction_id: `tx-${Date.now()}-TEST`,
    customer_email: 'john.doe@example.com',
    customer_ip: '203.0.113.45',
    amount: 299.99,
    currency: 'USD',
    merchant_id: 'merchant-042',
    card_bin: '424242',
    device_id: 'device-xyz789',
    timestamp: new Date().toISOString()
  };

  try {
    const result = await client.checkFraud(transaction);
    console.log(`Fraud Score: ${result.fraud_score}`);
    console.log(`Risk Level: ${result.risk_level}`);
    console.log(`Recommendation: ${result.recommendation}`);
  } catch (error) {
    console.error('Error checking fraud:', error.message);
  }
}

main();
```

### 3.3 PHP Integration

**Implementation:**
```php
<?php

class DYGSOMFraudClient {
    private $apiKey;
    private $baseURL = 'https://api.dygsom.pe';
    private $timeout = 5; // seconds

    public function __construct($apiKey = null) {
        $this->apiKey = $apiKey ?: getenv('DYGSOM_API_KEY');

        if (!$this->apiKey) {
            throw new Exception('API key is required');
        }
    }

    public function checkFraud($transaction) {
        $url = $this->baseURL . '/api/v1/fraud/score';

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($transaction));
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new Exception('API request failed: ' . $error);
        }

        if ($httpCode === 429) {
            throw new Exception('Rate limit exceeded');
        }

        if ($httpCode !== 200) {
            throw new Exception('API error: HTTP ' . $httpCode);
        }

        return json_decode($response, true);
    }
}

// Usage Example
$client = new DYGSOMFraudClient();

$transaction = [
    'transaction_id' => 'tx-' . time() . '-TEST',
    'customer_email' => 'john.doe@example.com',
    'customer_ip' => '203.0.113.45',
    'amount' => 299.99,
    'currency' => 'USD',
    'merchant_id' => 'merchant-042',
    'card_bin' => '424242',
    'device_id' => 'device-xyz789',
    'timestamp' => gmdate('Y-m-d\TH:i:s\Z')
];

try {
    $result = $client->checkFraud($transaction);
    echo "Fraud Score: " . $result['fraud_score'] . "\n";
    echo "Risk Level: " . $result['risk_level'] . "\n";
    echo "Recommendation: " . $result['recommendation'] . "\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

---

## Step 4: Handle Responses

Implement business logic based on fraud assessment recommendations.

### 4.1 Response Decision Tree

```python
def process_transaction(transaction):
    """Process transaction based on fraud assessment"""
    client = DYGSOMFraudClient()
    result = client.check_fraud(transaction)

    recommendation = result['recommendation']
    risk_level = result['risk_level']
    fraud_score = result['fraud_score']

    if recommendation == 'APPROVE':
        # Low risk - process normally
        return approve_transaction(transaction)

    elif recommendation == 'REVIEW':
        # Medium/High risk - manual review
        return queue_for_manual_review(transaction, result)

    elif recommendation == 'REJECT':
        # Critical risk - decline
        return decline_transaction(transaction, result)

    else:
        # Unknown recommendation - default to review
        return queue_for_manual_review(transaction, result)


def approve_transaction(transaction):
    """Process approved transaction"""
    # Complete payment processing
    # Send confirmation to customer
    # Update order status
    return {"status": "approved"}


def queue_for_manual_review(transaction, fraud_result):
    """Queue transaction for manual review"""
    # Store in review queue database
    # Notify fraud team
    # Send "pending review" message to customer
    return {"status": "pending_review", "fraud_score": fraud_result['fraud_score']}


def decline_transaction(transaction, fraud_result):
    """Decline high-risk transaction"""
    # Do not process payment
    # Log declined transaction
    # Send decline message to customer
    # Optional: Suggest alternative verification methods
    return {"status": "declined", "reason": "fraud_detected"}
```

### 4.2 Risk-Based Actions

| Risk Level | Recommendation | Suggested Actions |
|------------|----------------|-------------------|
| LOW | APPROVE | Process normally, no additional verification |
| MEDIUM | REVIEW | Request additional verification (CVV, 3DS), flag for review if high-value |
| HIGH | REVIEW | Mandatory manual review, request multiple verification factors |
| CRITICAL | REJECT | Decline transaction, block account temporarily, alert fraud team |

---

## Step 5: Implement Error Handling

Handle all possible error scenarios gracefully.

### 5.1 Comprehensive Error Handling

```python
import time
import logging

logger = logging.getLogger(__name__)

def check_fraud_with_error_handling(transaction, max_retries=3):
    """
    Check fraud with comprehensive error handling and retries.

    Args:
        transaction (dict): Transaction data
        max_retries (int): Maximum retry attempts

    Returns:
        dict: Fraud assessment or default safe response
    """
    client = DYGSOMFraudClient()

    for attempt in range(max_retries):
        try:
            result = client.check_fraud(transaction)
            return result

        except requests.Timeout:
            logger.warning(f"API timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            # On final timeout, return safe default
            return get_safe_default_response()

        except requests.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 401:
                logger.error("Invalid API key")
                raise  # Don't retry auth errors

            elif status_code == 422:
                logger.error("Invalid transaction data")
                raise  # Don't retry validation errors

            elif status_code == 429:
                logger.warning("Rate limit exceeded")
                retry_after = int(e.response.headers.get('Retry-After', 60))
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
                return get_safe_default_response()

            elif status_code >= 500:
                logger.error(f"Server error: {status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return get_safe_default_response()

            else:
                logger.error(f"Unexpected error: {status_code}")
                raise

        except Exception as e:
            logger.error(f"Unexpected exception: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return get_safe_default_response()

    return get_safe_default_response()


def get_safe_default_response():
    """
    Return safe default when API is unavailable.

    In case of API failure, default to REVIEW to ensure
    human oversight of potentially risky transactions.
    """
    return {
        "fraud_score": 0.5,
        "risk_level": "MEDIUM",
        "recommendation": "REVIEW",
        "factors": {},
        "processing_time_ms": 0,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fallback": True
    }
```

### 5.2 Circuit Breaker Pattern

For high-volume applications, implement circuit breaker to prevent cascading failures:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Circuit breaker for API calls"""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failures = 0
        self.state = 'CLOSED'

    def on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = 'OPEN'


# Usage
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def check_fraud_with_circuit_breaker(transaction):
    try:
        return circuit_breaker.call(client.check_fraud, transaction)
    except Exception as e:
        logger.error(f"Circuit breaker prevented call or call failed: {e}")
        return get_safe_default_response()
```

---

## Step 6: Test Your Integration

Thoroughly test before production deployment.

### 6.1 Test Checklist

- [ ] **Happy Path**: LOW risk transaction returns APPROVE
- [ ] **Medium Risk**: Transaction with elevated risk returns REVIEW
- [ ] **High Risk**: Suspicious transaction returns REJECT
- [ ] **Invalid Data**: Missing fields return 422 validation error
- [ ] **Invalid API Key**: Wrong key returns 401 unauthorized
- [ ] **Timeout Handling**: Request timeout handled gracefully
- [ ] **Rate Limiting**: 429 response triggers retry logic
- [ ] **Network Errors**: Connection failures handled properly
- [ ] **Logging**: All API calls logged with transaction IDs
- [ ] **Monitoring**: Error rates and latencies tracked

### 6.2 Test Scenarios

```python
def run_integration_tests():
    """Run comprehensive integration tests"""
    client = DYGSOMFraudClient()

    # Test 1: Valid low-risk transaction
    low_risk_tx = create_test_transaction(amount=50.00)
    result = client.check_fraud(low_risk_tx)
    assert result['risk_level'] == 'LOW'
    print("Test 1 PASSED: Low risk transaction")

    # Test 2: High-amount transaction
    high_amount_tx = create_test_transaction(amount=5000.00)
    result = client.check_fraud(high_amount_tx)
    assert result['risk_level'] in ['MEDIUM', 'HIGH']
    print("Test 2 PASSED: High amount transaction")

    # Test 3: Invalid email format
    try:
        invalid_tx = create_test_transaction()
        invalid_tx['customer_email'] = 'invalid-email'
        result = client.check_fraud(invalid_tx)
        assert False, "Should have raised validation error"
    except requests.HTTPError as e:
        assert e.response.status_code == 422
        print("Test 3 PASSED: Validation error handled")

    print("All integration tests passed")


def create_test_transaction(**overrides):
    """Create test transaction with optional overrides"""
    transaction = {
        "transaction_id": f"test-{int(time.time())}",
        "customer_email": "test@example.com",
        "customer_ip": "203.0.113.45",
        "amount": 99.99,
        "currency": "USD",
        "merchant_id": "merchant-test",
        "card_bin": "424242",
        "device_id": "device-test",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    transaction.update(overrides)
    return transaction
```

---

## Step 7: Go Live

Final steps before production deployment.

### 7.1 Pre-Launch Checklist

- [ ] **API Key**: Production API key generated and stored securely
- [ ] **Environment**: Production base URL configured (`https://api.dygsom.pe`)
- [ ] **HTTPS**: All requests use HTTPS (never HTTP)
- [ ] **Error Handling**: All error scenarios handled with fallback logic
- [ ] **Logging**: Comprehensive logging enabled
- [ ] **Monitoring**: Dashboards and alerts configured
- [ ] **Rate Limiting**: Retry logic with exponential backoff implemented
- [ ] **Timeout**: 5-second timeout configured
- [ ] **Testing**: All test scenarios passed in staging environment
- [ ] **Documentation**: Team familiar with integration and troubleshooting
- [ ] **Support**: Support contact information saved
- [ ] **Rollback Plan**: Procedure to disable integration if issues occur

### 7.2 Launch Day

1. **Deploy to Production** during low-traffic period
2. **Monitor Closely** for first 24 hours:
   - API response times (target: <100ms P95)
   - Error rates (target: <0.1%)
   - Fraud detection accuracy
   - Business metrics (approval/review/decline rates)
3. **Verify** fraud assessments align with expectations
4. **Review** first 50-100 transactions manually
5. **Adjust** risk thresholds if needed based on business requirements

### 7.3 Post-Launch Monitoring

Monitor these metrics continuously:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Latency (P95) | <100ms | >150ms |
| Error Rate | <0.1% | >1% |
| Approval Rate | 70-85% | <60% or >95% |
| Review Rate | 10-25% | >40% |
| Decline Rate | 5-10% | >15% |

---

## Next Steps

- Review [Best Practices](../customer/BEST_PRACTICES.md)
- Set up [Monitoring](../operations/MONITORING_GUIDE.md)
- Read [Error Codes](ERROR_CODES.md) documentation
- Join [Community Slack](https://slack.dygsom.pe)
- Contact [Support](mailto:support@dygsom.pe) with questions

---

**Need Help?**

- Email: support@dygsom.pe
- Documentation: https://docs.dygsom.pe
- Status Page: https://status.dygsom.pe

**Last Updated:** 2025-01-25
**Version:** 1.0.0
