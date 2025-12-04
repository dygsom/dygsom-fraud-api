"""
DYGSOM Fraud API - Python Integration Example

This example demonstrates how to integrate the DYGSOM Fraud Detection API
into a Python application with proper error handling and best practices.

Requirements:
    pip install requests python-dotenv

Usage:
    export DYGSOM_API_KEY=your_api_key_here
    python python_example.py
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DYGSOMFraudClient:
    """
    Client for DYGSOM Fraud Detection API.

    This client provides a simple interface to check transactions for fraud
    with built-in error handling, retries, and logging.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.dygsom.pe"):
        """
        Initialize the fraud client.

        Args:
            api_key: DYGSOM API key (defaults to DYGSOM_API_KEY env var)
            base_url: API base URL (defaults to production)
        """
        self.api_key = api_key or os.getenv("DYGSOM_API_KEY")
        self.base_url = base_url.rstrip('/')
        self.timeout = 5  # seconds

        if not self.api_key:
            raise ValueError("API key is required. Set DYGSOM_API_KEY environment variable.")

        logger.info(f"Initialized DYGSOM client with base URL: {self.base_url}")

    def check_fraud(self, transaction: Dict) -> Dict:
        """
        Check a transaction for fraud.

        Args:
            transaction: Transaction data dictionary

        Returns:
            dict: Fraud assessment result containing:
                - fraud_score (float): 0.0 to 1.0
                - risk_level (str): LOW, MEDIUM, HIGH, or CRITICAL
                - recommendation (str): APPROVE, REVIEW, or REJECT
                - factors (dict): Risk factor breakdown
                - processing_time_ms (int): API processing time
                - timestamp (str): Response timestamp

        Raises:
            requests.HTTPError: On API error
            requests.Timeout: On request timeout
            requests.RequestException: On network error
        """
        url = f"{self.base_url}/api/v1/fraud/score"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

        logger.info(f"Checking fraud for transaction: {transaction.get('transaction_id')}")

        try:
            response = requests.post(
                url,
                json=transaction,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Fraud check complete: {result['risk_level']} (score: {result['fraud_score']})")

            return result

        except requests.Timeout:
            logger.error("API request timed out")
            raise

        except requests.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"API returned error: {status_code}")

            if status_code == 401:
                raise Exception("Invalid API key. Check your credentials.")
            elif status_code == 422:
                error_data = e.response.json()
                raise Exception(f"Validation error: {error_data}")
            elif status_code == 429:
                raise Exception("Rate limit exceeded. Retry after 60 seconds.")
            else:
                raise

        except requests.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise

    def check_fraud_with_retry(self, transaction: Dict, max_retries: int = 3) -> Dict:
        """
        Check fraud with automatic retry logic.

        Args:
            transaction: Transaction data
            max_retries: Maximum number of retry attempts

        Returns:
            dict: Fraud assessment result or safe default on failure
        """
        for attempt in range(max_retries):
            try:
                return self.check_fraud(transaction)

            except requests.Timeout:
                logger.warning(f"Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

        # If all retries fail, return safe default (REVIEW)
        logger.warning("All retry attempts failed. Returning safe default response.")
        return self._get_safe_default()

    def _get_safe_default(self) -> Dict:
        """Return safe default response when API is unavailable."""
        return {
            "fraud_score": 0.5,
            "risk_level": "MEDIUM",
            "recommendation": "REVIEW",
            "factors": {
                "velocity_score": 0.0,
                "amount_risk": 0.0,
                "location_risk": 0.0,
                "device_risk": 0.0
            },
            "processing_time_ms": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "fallback": True
        }


def process_transaction(transaction: Dict) -> Dict:
    """
    Process a transaction based on fraud assessment.

    Args:
        transaction: Transaction data

    Returns:
        dict: Processing result with status
    """
    client = DYGSOMFraudClient()

    try:
        # Check fraud with retry logic
        result = client.check_fraud_with_retry(transaction)

        # Handle recommendation
        recommendation = result['recommendation']

        if recommendation == 'APPROVE':
            logger.info("Transaction APPROVED - processing payment")
            return {
                "status": "approved",
                "transaction_id": transaction['transaction_id'],
                "fraud_score": result['fraud_score']
            }

        elif recommendation == 'REVIEW':
            logger.warning("Transaction requires REVIEW - queuing for manual review")
            return {
                "status": "pending_review",
                "transaction_id": transaction['transaction_id'],
                "fraud_score": result['fraud_score']
            }

        elif recommendation == 'REJECT':
            logger.error("Transaction REJECTED - high fraud risk")
            return {
                "status": "declined",
                "transaction_id": transaction['transaction_id'],
                "fraud_score": result['fraud_score'],
                "reason": "fraud_detected"
            }

    except Exception as e:
        logger.error(f"Failed to process transaction: {str(e)}")
        # On error, default to manual review for safety
        return {
            "status": "error_review_required",
            "transaction_id": transaction['transaction_id'],
            "error": str(e)
        }


def create_example_transaction() -> Dict:
    """Create an example transaction for testing."""
    timestamp_ms = int(time.time() * 1000)
    return {
        "transaction_id": f"tx-{timestamp_ms}-EXAMPLE",
        "customer_email": "john.doe@example.com",
        "customer_ip": "203.0.113.45",
        "amount": 299.99,
        "currency": "USD",
        "merchant_id": "merchant-042",
        "card_bin": "424242",
        "device_id": "device-xyz789",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def main():
    """Main execution function."""
    print("=" * 60)
    print("DYGSOM Fraud API - Python Example")
    print("=" * 60)
    print()

    # Create example transaction
    transaction = create_example_transaction()

    print("Transaction Details:")
    print(f"  ID: {transaction['transaction_id']}")
    print(f"  Email: {transaction['customer_email']}")
    print(f"  Amount: {transaction['currency']} {transaction['amount']}")
    print()

    # Process transaction
    print("Processing transaction...")
    result = process_transaction(transaction)

    print()
    print("Result:")
    print(f"  Status: {result['status']}")
    print(f"  Fraud Score: {result.get('fraud_score', 'N/A')}")
    print()

    print("=" * 60)


if __name__ == "__main__":
    main()
