# Quick Start Guide

**Estimated Time:** 15 minutes
**Difficulty:** Beginner
**Version:** 1.0.0

Get started with the DYGSOM Fraud Detection API in three simple steps.

## Prerequisites

- API key (sign up at https://dygsom.com/signup)
- Development environment with internet access
- cURL, Python, Node.js, or PHP installed

---

## Step 1: Get Your API Key (2 minutes)

1. Sign up at [https://dygsom.com/signup](https://dygsom.com/signup)
2. Verify your email address
3. Log in to your dashboard
4. Navigate to **API Keys** section
5. Click **Generate New Key**
6. Copy the API key (format: `dygsom_...`)
7. Store it securely

**Store as environment variable:**
```bash
export DYGSOM_API_KEY=dygsom_your_api_key_here
```

---

## Step 2: Test the API (3 minutes)

Test your API key with a simple cURL request:

```bash
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DYGSOM_API_KEY" \
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

If you see this response, your API key works correctly.

---

## Step 3: Integrate Into Your Code (10 minutes)

Choose your language and integrate the fraud check into your application.

### Python Example

```python
import os
import requests
from datetime import datetime

API_KEY = os.getenv("DYGSOM_API_KEY")
API_URL = "https://api.dygsom.com/api/v1/fraud/score"

def check_fraud(transaction):
    response = requests.post(
        API_URL,
        json=transaction,
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return response.json()

# Example usage
transaction = {
    "transaction_id": "tx-123456",
    "customer_email": "user@example.com",
    "customer_ip": "203.0.113.45",
    "amount": 299.99,
    "currency": "USD",
    "merchant_id": "merchant-001",
    "card_bin": "424242",
    "device_id": "device-xyz789",
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

result = check_fraud(transaction)

if result["recommendation"] == "APPROVE":
    print("Transaction approved - process payment")
elif result["recommendation"] == "REVIEW":
    print("Transaction flagged - manual review required")
else:
    print("Transaction declined - high fraud risk")
```

### Node.js Example

```javascript
const axios = require('axios');

const API_KEY = process.env.DYGSOM_API_KEY;
const API_URL = 'https://api.dygsom.com/api/v1/fraud/score';

async function checkFraud(transaction) {
  const response = await axios.post(API_URL, transaction, {
    headers: { 'X-API-Key': API_KEY },
    timeout: 5000
  });
  return response.data;
}

// Example usage
const transaction = {
  transaction_id: `tx-${Date.now()}`,
  customer_email: 'user@example.com',
  customer_ip: '203.0.113.45',
  amount: 299.99,
  currency: 'USD',
  merchant_id: 'merchant-001',
  card_bin: '424242',
  device_id: 'device-xyz789',
  timestamp: new Date().toISOString()
};

const result = await checkFraud(transaction);

if (result.recommendation === 'APPROVE') {
  console.log('Transaction approved');
} else if (result.recommendation === 'REVIEW') {
  console.log('Manual review required');
} else {
  console.log('Transaction declined');
}
```

---

## Next Steps

1. **Read Full Integration Guide** - [docs/api/INTEGRATION_GUIDE.md](../api/INTEGRATION_GUIDE.md)
2. **Review Best Practices** - [docs/customer/BEST_PRACTICES.md](BEST_PRACTICES.md)
3. **Complete Integration Checklist** - [docs/customer/INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md)
4. **Test Thoroughly** - [docs/customer/TESTING_GUIDE.md](TESTING_GUIDE.md)
5. **Go Live** - [docs/customer/GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md)

---

## Need Help?

- **Email:** support@dygsom.com
- **Documentation:** https://docs.dygsom.com
- **API Reference:** [docs/api/API_REFERENCE.md](../api/API_REFERENCE.md)
- **Code Examples:** [docs/api/examples/](../api/examples/)

---

**Version:** 1.0.0
**Last Updated:** 2025-01-25
