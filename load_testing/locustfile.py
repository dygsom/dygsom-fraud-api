"""
Locust load testing for DYGSOM Fraud API.

This file defines the main load test scenarios for the Fraud Detection API.
It simulates realistic user behavior with weighted tasks.

Usage:
    # Baseline test (10 users, 5 minutes)
    locust -f locustfile.py --host=http://localhost:3000 \
           --users 10 --spawn-rate 2 --run-time 5m --headless

    # Stress test (100 users, 10 minutes)
    locust -f locustfile.py --host=http://localhost:3000 \
           --users 100 --spawn-rate 10 --run-time 10m --headless

    # With Web UI
    locust -f locustfile.py --host=http://localhost:3000
"""

import random
import string
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner

# API Key for authentication (update with your actual API key)
API_KEY = "dygsom_test_api_key_change_me"


class FraudAPIUser(HttpUser):
    """
    Simulates a user making requests to the Fraud Detection API.

    Tasks are weighted based on realistic usage patterns:
    - Fraud scoring is the main use case (weight 10)
    - Health checks are less frequent (weight 2-1)
    """

    # Wait time between requests (1-3 seconds)
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts."""
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }

    @task(10)
    def score_transaction(self):
        """
        Main task: Score a transaction for fraud detection.

        Weight: 10 (most common operation)
        Expected: 200 OK, <100ms P95
        """
        payload = {
            "transaction_id": f"tx-{self._generate_transaction_id()}",
            "customer_email": self._generate_email(),
            "customer_ip": self._generate_ip(),
            "amount": round(random.uniform(10.0, 5000.0), 2),
            "currency": random.choice(["USD", "EUR", "PEN", "GBP"]),
            "merchant_id": f"merchant-{random.randint(1, 100)}",
            "card_bin": self._generate_card_bin(),
            "device_id": f"device-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow().isoformat()
        }

        with self.client.post(
            "/api/v1/fraud/score",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/fraud/score"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "fraud_score" in data and "risk_level" in data:
                        response.success()
                    else:
                        response.failure("Missing required fields in response")
                except Exception as e:
                    response.failure(f"Invalid JSON response: {e}")
            elif response.status_code == 401:
                response.failure("Authentication failed - check API key")
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(2)
    def health_check(self):
        """
        Health check task: Basic liveness check.

        Weight: 2 (occasional monitoring)
        Expected: 200 OK, <10ms
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)
    def health_ready(self):
        """
        Readiness check task: Verify all dependencies are ready.

        Weight: 1 (less frequent, more expensive)
        Expected: 200 OK, <50ms
        """
        with self.client.get(
            "/health/ready",
            catch_response=True,
            name="/health/ready"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Readiness check failed: {response.status_code}")

    # Helper methods for generating realistic test data

    def _generate_transaction_id(self):
        """Generate a unique transaction ID."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{timestamp}-{random_suffix}"

    def _generate_email(self):
        """Generate a realistic email address."""
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"]
        username = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
        return f"{username}@{random.choice(domains)}"

    def _generate_ip(self):
        """Generate a realistic IP address."""
        # Generate IPs in common ranges
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def _generate_card_bin(self):
        """Generate a realistic card BIN (first 6 digits)."""
        # Common BINs for testing
        bins = ["424242", "400000", "510000", "340000", "370000"]
        return random.choice(bins)


# Event handlers for logging and reporting

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Log failed requests for debugging.

    This helps identify which specific requests are failing during load tests.
    """
    if exception:
        print(f"❌ Request failed: {request_type} {name}")
        print(f"   Exception: {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Print test start information.

    Called once when the test starts (useful for logging).
    """
    print("=" * 80)
    print("🚀 Load Test Starting")
    print("=" * 80)
    print(f"Target Host: {environment.host}")
    print(f"Start Time: {datetime.utcnow().isoformat()}")

    if isinstance(environment.runner, MasterRunner):
        print(f"Mode: Master")
    elif isinstance(environment.runner, WorkerRunner):
        print(f"Mode: Worker")
    else:
        print(f"Mode: Standalone")

    print("=" * 80)
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Print test summary when test stops.

    Displays key metrics: requests, failures, RPS, response times.
    """
    print()
    print("=" * 80)
    print("✅ Load Test Complete")
    print("=" * 80)

    stats = environment.stats

    # Total requests
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    print(f"Total Requests: {total_requests:,}")
    print(f"Total Failures: {total_failures:,} ({failure_rate:.2f}%)")

    # RPS
    if stats.total.total_response_time > 0:
        rps = stats.total.current_rps
        print(f"Requests/sec: {rps:.2f}")

    # Response times
    print()
    print("Response Times:")
    print(f"  Average: {stats.total.avg_response_time:.2f}ms")
    print(f"  Median:  {stats.total.median_response_time:.2f}ms")

    if stats.total.get_response_time_percentile(0.95):
        print(f"  P95:     {stats.total.get_response_time_percentile(0.95):.2f}ms")
    if stats.total.get_response_time_percentile(0.99):
        print(f"  P99:     {stats.total.get_response_time_percentile(0.99):.2f}ms")

    print(f"  Min:     {stats.total.min_response_time:.2f}ms")
    print(f"  Max:     {stats.total.max_response_time:.2f}ms")

    # Per-endpoint breakdown
    print()
    print("Per-Endpoint Stats:")
    print("-" * 80)
    print(f"{'Endpoint':<40} {'Requests':<12} {'Failures':<12} {'Avg (ms)':<10}")
    print("-" * 80)

    for entry in stats.entries.values():
        if entry.num_requests > 0:
            endpoint_failure_rate = (entry.num_failures / entry.num_requests * 100) if entry.num_requests > 0 else 0
            print(f"{entry.name:<40} {entry.num_requests:<12} {entry.num_failures:<12} {entry.avg_response_time:<10.2f}")

    print("=" * 80)
    print()

    # Performance targets check
    print("Performance Targets Check:")
    print("-" * 80)

    p95 = stats.total.get_response_time_percentile(0.95) or 0
    p99 = stats.total.get_response_time_percentile(0.99) or 0

    # Targets
    p95_target = 100  # ms
    p99_target = 200  # ms
    error_rate_target = 0.1  # %

    p95_status = "✅ PASS" if p95 <= p95_target else "❌ FAIL"
    p99_status = "✅ PASS" if p99 <= p99_target else "❌ FAIL"
    error_status = "✅ PASS" if failure_rate <= error_rate_target else "❌ FAIL"

    print(f"P95 Latency:  {p95:.2f}ms / {p95_target}ms  {p95_status}")
    print(f"P99 Latency:  {p99:.2f}ms / {p99_target}ms  {p99_status}")
    print(f"Error Rate:   {failure_rate:.2f}% / {error_rate_target}%  {error_status}")

    print("=" * 80)
    print()
