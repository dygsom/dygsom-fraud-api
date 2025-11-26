"""
Specialized load test scenario for Fraud Scoring endpoint.

This scenario tests the fraud scoring endpoint with different transaction amounts
to validate performance across various risk profiles.

Usage:
    locust -f scenarios/fraud_scoring.py --host=http://localhost:3000 \
           --users 100 --spawn-rate 10 --run-time 10m --headless

Targets:
    - P95 Latency: <100ms
    - P99 Latency: <200ms
    - Error Rate: <0.1%
    - Throughput: 100+ req/sec per instance
"""

import random
import string
from datetime import datetime
from locust import HttpUser, task, constant_throughput

# API Key for authentication
API_KEY = "dygsom_test_api_key_change_me"


class FraudScoringLoadTest(HttpUser):
    """
    Focused load test for fraud scoring endpoint.

    Tests three transaction amount ranges to validate performance
    across low, medium, and high-value transactions.

    This uses constant_throughput to aim for 100 req/sec.
    """

    # Target 100 requests per second across all users
    # With 100 users, each user makes 1 request per second
    wait_time = constant_throughput(100)

    def on_start(self):
        """Initialize headers with API key."""
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }

    @task(5)
    def score_low_amount(self):
        """
        Test fraud scoring with low transaction amounts (<100 currency units).

        Weight: 5 (common in real-world scenarios)
        Expected Risk: Typically LOW
        Expected Latency: <50ms
        """
        payload = {
            "transaction_id": self._generate_transaction_id(),
            "customer_email": self._generate_email(),
            "customer_ip": self._generate_ip(),
            "amount": round(random.uniform(1.0, 99.99), 2),
            "currency": "PEN",
            "merchant_id": f"merchant-{random.randint(1, 50)}",
            "card_bin": "424242",
            "device_id": f"device-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow().isoformat()
        }

        self._score_transaction(payload, "low_amount")

    @task(3)
    def score_medium_amount(self):
        """
        Test fraud scoring with medium transaction amounts (100-1000 currency units).

        Weight: 3 (moderate frequency)
        Expected Risk: Varies (LOW to MEDIUM)
        Expected Latency: <75ms
        """
        payload = {
            "transaction_id": self._generate_transaction_id(),
            "customer_email": self._generate_email(),
            "customer_ip": self._generate_ip(),
            "amount": round(random.uniform(100.0, 999.99), 2),
            "currency": "USD",
            "merchant_id": f"merchant-{random.randint(1, 50)}",
            "card_bin": "510000",
            "device_id": f"device-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow().isoformat()
        }

        self._score_transaction(payload, "medium_amount")

    @task(2)
    def score_high_amount(self):
        """
        Test fraud scoring with high transaction amounts (>1000 currency units).

        Weight: 2 (less frequent, but critical for fraud detection)
        Expected Risk: Varies (MEDIUM to HIGH)
        Expected Latency: <100ms
        """
        payload = {
            "transaction_id": self._generate_transaction_id(),
            "customer_email": self._generate_email(),
            "customer_ip": self._generate_ip(),
            "amount": round(random.uniform(1000.0, 10000.0), 2),
            "currency": "EUR",
            "merchant_id": f"merchant-{random.randint(1, 50)}",
            "card_bin": "340000",
            "device_id": f"device-{random.randint(1000, 9999)}",
            "timestamp": datetime.utcnow().isoformat()
        }

        self._score_transaction(payload, "high_amount")

    @task(1)
    def score_suspicious_pattern(self):
        """
        Test fraud scoring with potentially suspicious patterns.

        Weight: 1 (less frequent)
        Features:
            - High amount
            - New customer (random email)
            - Multiple rapid transactions (simulated by using similar patterns)

        Expected Risk: HIGH or CRITICAL
        Expected Latency: <100ms
        """
        # Use a suspicious pattern: high amount + short email
        suspicious_email = f"user{random.randint(1, 100)}@temp.com"

        payload = {
            "transaction_id": self._generate_transaction_id(),
            "customer_email": suspicious_email,
            "customer_ip": self._generate_ip(),
            "amount": round(random.uniform(5000.0, 15000.0), 2),
            "currency": "USD",
            "merchant_id": f"merchant-{random.randint(90, 100)}",  # Less common merchants
            "card_bin": "400000",
            "device_id": f"device-{random.randint(1, 100)}",  # Reused device IDs
            "timestamp": datetime.utcnow().isoformat()
        }

        self._score_transaction(payload, "suspicious_pattern")

    def _score_transaction(self, payload, scenario_name):
        """
        Internal method to score a transaction with proper error handling.

        Args:
            payload: Transaction data
            scenario_name: Name of the scenario for tracking
        """
        with self.client.post(
            "/api/v1/fraud/score",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name=f"/api/v1/fraud/score ({scenario_name})"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response structure
                    required_fields = ["fraud_score", "risk_level", "recommendation"]
                    if all(field in data for field in required_fields):
                        # Validate data types
                        if not isinstance(data["fraud_score"], (int, float)):
                            response.failure("fraud_score is not a number")
                        elif data["fraud_score"] < 0 or data["fraud_score"] > 1:
                            response.failure("fraud_score out of range [0, 1]")
                        elif data["risk_level"] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                            response.failure(f"Invalid risk_level: {data['risk_level']}")
                        elif data["recommendation"] not in ["APPROVE", "REVIEW", "REJECT"]:
                            response.failure(f"Invalid recommendation: {data['recommendation']}")
                        else:
                            response.success()
                    else:
                        missing = [f for f in required_fields if f not in data]
                        response.failure(f"Missing fields in response: {missing}")
                except Exception as e:
                    response.failure(f"Invalid JSON response: {e}")
            elif response.status_code == 401:
                response.failure("Authentication failed - check API key")
            elif response.status_code == 422:
                response.failure("Validation error - invalid payload")
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    # Helper methods

    def _generate_transaction_id(self):
        """Generate a unique transaction ID."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"perf-{timestamp}-{random_suffix}"

    def _generate_email(self):
        """Generate a realistic email address with variety."""
        domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "example.com", "test.com", "demo.com", "temp.com"
        ]
        username_length = random.randint(5, 15)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
        return f"{username}@{random.choice(domains)}"

    def _generate_ip(self):
        """
        Generate realistic IP addresses.

        Returns IPs from common ranges to simulate realistic traffic patterns.
        """
        # Common IP ranges for testing
        ip_ranges = [
            (192, 168, random.randint(0, 255), random.randint(1, 254)),  # Private
            (10, random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)),  # Private
            (172, random.randint(16, 31), random.randint(0, 255), random.randint(1, 254)),  # Private
            (8, 8, random.randint(0, 255), random.randint(1, 254)),  # Google DNS range
            (1, 1, random.randint(0, 255), random.randint(1, 254)),  # Cloudflare range
        ]

        ip_tuple = random.choice(ip_ranges)
        return f"{ip_tuple[0]}.{ip_tuple[1]}.{ip_tuple[2]}.{ip_tuple[3]}"
