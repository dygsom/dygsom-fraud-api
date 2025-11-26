#!/bin/bash

################################################################################
# Smoke Tests for DYGSOM Fraud API
# Usage: ./smoke-tests.sh [staging|production]
#
# This script runs critical smoke tests post-deployment:
# 1. GET /health (200 OK)
# 2. GET /health/ready (200 OK)
# 3. GET /metrics (200 OK)
# 4. POST /api/v1/fraud/score with API key (200 OK)
# 5. POST /api/v1/fraud/score without API key (401 Unauthorized)
#
# Exit code 0 if all tests pass, 1 if any test fails
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=5

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_test() {
    echo -e "${YELLOW}🧪 TEST: $1${NC}"
}

print_usage() {
    echo "Usage: $0 [staging|production]"
    echo ""
    echo "Arguments:"
    echo "  environment  - Target environment (staging or production)"
    echo ""
    echo "Environment variables:"
    echo "  TEST_API_KEY - Valid API key for authenticated tests (required for production)"
    echo ""
    echo "Examples:"
    echo "  $0 staging"
    echo "  TEST_API_KEY=dygsom_xxx $0 production"
    exit 1
}

run_test() {
    local test_name=$1
    local expected_status=$2
    local method=$3
    local url=$4
    local headers=$5
    local data=$6

    log_test "$test_name"

    # Build curl command
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"

    if [ -n "$headers" ]; then
        curl_cmd="$curl_cmd $headers"
    fi

    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi

    curl_cmd="$curl_cmd '$url'"

    # Execute request
    local response=$(eval $curl_cmd)
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    # Check status code
    if [ "$status_code" == "$expected_status" ]; then
        log_success "$test_name - Expected: $expected_status, Got: $status_code"
        return 0
    else
        log_error "$test_name - Expected: $expected_status, Got: $status_code"
        echo "Response body: $body"
        return 1
    fi
}

################################################################################
# Smoke Tests
################################################################################

test_health() {
    local base_url=$1

    run_test \
        "Health Check (Liveness)" \
        "200" \
        "GET" \
        "${base_url}/health"
}

test_health_ready() {
    local base_url=$1

    run_test \
        "Health Check (Readiness)" \
        "200" \
        "GET" \
        "${base_url}/health/ready"
}

test_metrics() {
    local base_url=$1

    run_test \
        "Prometheus Metrics Endpoint" \
        "200" \
        "GET" \
        "${base_url}/metrics"
}

test_fraud_score_with_auth() {
    local base_url=$1
    local api_key=$2

    if [ -z "$api_key" ]; then
        log_error "Fraud Score (Authenticated) - No API key provided"
        return 1
    fi

    local test_payload='{
        "transaction_id": "smoke-test-'$(date +%s)'",
        "customer_email": "smoke-test@example.com",
        "customer_ip": "192.168.1.100",
        "amount": 100.50,
        "currency": "USD",
        "merchant_id": "test-merchant",
        "card_bin": "424242"
    }'

    run_test \
        "Fraud Score (Authenticated)" \
        "200" \
        "POST" \
        "${base_url}/api/v1/fraud/score" \
        "-H 'Content-Type: application/json' -H 'X-API-Key: ${api_key}'" \
        "$test_payload"
}

test_fraud_score_without_auth() {
    local base_url=$1

    local test_payload='{
        "transaction_id": "smoke-test-'$(date +%s)'",
        "customer_email": "smoke-test@example.com",
        "customer_ip": "192.168.1.100",
        "amount": 100.50,
        "currency": "USD",
        "merchant_id": "test-merchant",
        "card_bin": "424242"
    }'

    run_test \
        "Fraud Score (Unauthenticated - Should Fail)" \
        "401" \
        "POST" \
        "${base_url}/api/v1/fraud/score" \
        "-H 'Content-Type: application/json'" \
        "$test_payload"
}

################################################################################
# Main Logic
################################################################################

main() {
    # Validate arguments
    if [ $# -lt 1 ]; then
        log_error "Missing required arguments"
        print_usage
    fi

    ENVIRONMENT=$1

    # Validate environment
    if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
        log_error "Invalid environment: $ENVIRONMENT"
        print_usage
    fi

    # Set base URL based on environment
    if [ "$ENVIRONMENT" == "staging" ]; then
        BASE_URL="http://localhost:3000"
    else
        BASE_URL="http://localhost:3000"
    fi

    log_info "=========================================="
    log_info "  DYGSOM Fraud API - Smoke Tests"
    log_info "=========================================="
    log_info "Environment: $ENVIRONMENT"
    log_info "Base URL: $BASE_URL"
    log_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "=========================================="
    echo ""

    # Run tests
    test_health "$BASE_URL" || true
    echo ""

    test_health_ready "$BASE_URL" || true
    echo ""

    test_metrics "$BASE_URL" || true
    echo ""

    # For authenticated tests, check if API key is available
    if [ -z "$TEST_API_KEY" ]; then
        log_error "TEST_API_KEY environment variable not set"
        log_error "Skipping authenticated fraud score test"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        test_fraud_score_with_auth "$BASE_URL" "$TEST_API_KEY" || true
    fi
    echo ""

    test_fraud_score_without_auth "$BASE_URL" || true
    echo ""

    # Summary
    log_info "=========================================="
    log_info "  Test Results Summary"
    log_info "=========================================="
    log_info "Total Tests: $TOTAL_TESTS"
    log_success "Passed: $TESTS_PASSED"

    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Failed: $TESTS_FAILED"
        log_info "=========================================="
        echo ""
        exit 1
    else
        log_info "Failed: $TESTS_FAILED"
        log_info "=========================================="
        echo ""
        log_success "All smoke tests passed! ✨"
        exit 0
    fi
}

# Run main function
main "$@"
