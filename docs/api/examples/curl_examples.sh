#!/bin/bash
#
# DYGSOM Fraud API - cURL Examples
#
# This script demonstrates various API calls using cURL.
# Set your API key before running:
#   export DYGSOM_API_KEY=your_api_key_here
#

API_KEY="${DYGSOM_API_KEY}"
BASE_URL="https://api.dygsom.com"

if [ -z "$API_KEY" ]; then
    echo "Error: DYGSOM_API_KEY environment variable not set"
    exit 1
fi

echo "======================================================================"
echo "DYGSOM Fraud API - cURL Examples"
echo "======================================================================"
echo

# Example 1: Health Check
echo "1. Health Check"
echo "----------------------------------------------------------------------"
curl -X GET "$BASE_URL/health"
echo
echo

# Example 2: Readiness Check
echo "2. Readiness Check"
echo "----------------------------------------------------------------------"
curl -X GET "$BASE_URL/health/ready"
echo
echo

# Example 3: Fraud Score - Low Risk Transaction
echo "3. Fraud Score - Low Risk Transaction"
echo "----------------------------------------------------------------------"
curl -X POST "$BASE_URL/api/v1/fraud/score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "transaction_id": "tx-'$(date +%s)'000-LOW",
    "customer_email": "john.doe@example.com",
    "customer_ip": "203.0.113.45",
    "amount": 49.99,
    "currency": "USD",
    "merchant_id": "merchant-001",
    "card_bin": "424242",
    "device_id": "device-xyz789",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
echo
echo

# Example 4: Fraud Score - High Amount Transaction
echo "4. Fraud Score - High Amount Transaction"
echo "----------------------------------------------------------------------"
curl -X POST "$BASE_URL/api/v1/fraud/score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "transaction_id": "tx-'$(date +%s)'000-HIGH",
    "customer_email": "suspicious@temp.com",
    "customer_ip": "198.51.100.42",
    "amount": 5000.00,
    "currency": "USD",
    "merchant_id": "merchant-099",
    "card_bin": "400000",
    "device_id": "device-suspicious",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
echo
echo

# Example 5: Validation Error (Invalid Email)
echo "5. Validation Error Example"
echo "----------------------------------------------------------------------"
curl -X POST "$BASE_URL/api/v1/fraud/score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "transaction_id": "tx-'$(date +%s)'000-ERR",
    "customer_email": "invalid-email",
    "customer_ip": "203.0.113.45",
    "amount": 99.99,
    "currency": "USD",
    "merchant_id": "merchant-001",
    "card_bin": "424242",
    "device_id": "device-test",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
echo
echo

echo "======================================================================"
echo "Examples Complete"
echo "======================================================================"
