"""
Seed script to populate database with 1000 test transactions.
Generates realistic transaction data with varying fraud scores for testing.
"""

import asyncio
from faker import Faker
from prisma import Prisma
import random
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Faker with Spanish locale
fake = Faker(["es_ES"])  # Spanish Spain locale (Peru not available)

# Constants for transaction generation
TOTAL_TRANSACTIONS = 1000
LEGITIMATE_COUNT = 800  # 80% - fraud_score < 0.3
SUSPICIOUS_COUNT = 150  # 15% - 0.3 <= fraud_score < 0.8
FRAUDULENT_COUNT = 50  # 5% - fraud_score >= 0.8

# Transaction amount ranges (in PEN)
LEGITIMATE_AMOUNT_RANGE = (10.0, 2000.0)
SUSPICIOUS_AMOUNT_RANGE = (1000.0, 5000.0)
FRAUDULENT_AMOUNT_RANGE = (3000.0, 10000.0)

# Card BINs for different card types
CARD_BINS = {
    "Visa": ["411111", "424242", "400000", "450000", "470000"],
    "Mastercard": ["555555", "540000", "530000", "520000"],
    "Amex": ["378282", "371449", "370000"],
}

# Risk levels based on fraud score
RISK_LEVEL_LOW = "LOW"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_CRITICAL = "CRITICAL"

# Decisions based on risk level
DECISION_APPROVE = "APPROVE"
DECISION_REVIEW = "REVIEW"
DECISION_DECLINE = "DECLINE"


def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    return f"txn_{fake.uuid4()[:12]}"


def generate_email(fraud_type: str) -> str:
    """Generate email based on fraud type

    Args:
        fraud_type: Type of transaction (legitimate, suspicious, fraudulent)

    Returns:
        Email address string
    """
    if fraud_type == "fraudulent":
        # Fraudulent emails often use disposable domains
        disposable_domains = ["tempmail.com", "throwaway.email", "guerrillamail.com"]
        username = fake.user_name()
        domain = random.choice(disposable_domains)
        return f"{username}@{domain}"
    else:
        # Legitimate emails use common providers
        return fake.email()


def generate_ip_address(fraud_type: str) -> str:
    """Generate IP address based on fraud type

    Args:
        fraud_type: Type of transaction (legitimate, suspicious, fraudulent)

    Returns:
        IP address string
    """
    if fraud_type == "fraudulent":
        # Fraudulent IPs often from suspicious regions or VPNs
        # Using ranges that are commonly associated with VPNs/proxies
        return (
            f"{random.choice([45, 91, 185])}.{random.randint(0, 255)}."
            f"{random.randint(0, 255)}.{random.randint(1, 254)}"
        )
    else:
        # Legitimate IPs from common ISPs in Peru
        # Peru ISP ranges: 181.x, 190.x, 200.x
        return (
            f"{random.choice([181, 190, 200])}.{random.randint(0, 255)}."
            f"{random.randint(0, 255)}.{random.randint(1, 254)}"
        )


def generate_card_data() -> dict:
    """Generate card payment method data

    Returns:
        Dict with card_bin, card_last4, card_brand
    """
    brand = random.choice(list(CARD_BINS.keys()))
    bin_number = random.choice(CARD_BINS[brand])
    last4 = f"{random.randint(0, 9999):04d}"

    return {"card_bin": bin_number, "card_last4": last4, "card_brand": brand}


def calculate_risk_level(fraud_score: float) -> str:
    """Calculate risk level based on fraud score

    Args:
        fraud_score: Fraud score (0-1)

    Returns:
        Risk level string
    """
    if fraud_score < 0.3:
        return RISK_LEVEL_LOW
    elif fraud_score < 0.5:
        return RISK_LEVEL_MEDIUM
    elif fraud_score < 0.8:
        return RISK_LEVEL_HIGH
    else:
        return RISK_LEVEL_CRITICAL


def calculate_decision(risk_level: str, fraud_score: float) -> str:
    """Calculate decision based on risk level and fraud score

    Args:
        risk_level: Risk level string
        fraud_score: Fraud score (0-1)

    Returns:
        Decision string
    """
    if risk_level == RISK_LEVEL_LOW:
        return DECISION_APPROVE
    elif risk_level == RISK_LEVEL_MEDIUM:
        return DECISION_REVIEW
    elif risk_level == RISK_LEVEL_HIGH:
        return DECISION_REVIEW if fraud_score < 0.7 else DECISION_DECLINE
    else:  # CRITICAL
        return DECISION_DECLINE


def generate_transaction(fraud_type: str, index: int) -> dict:
    """Generate a single transaction with specified fraud type

    Args:
        fraud_type: Type of transaction (legitimate, suspicious, fraudulent)
        index: Transaction index for uniqueness

    Returns:
        Dict with transaction data
    """
    # Determine fraud score and amount based on type
    if fraud_type == "legitimate":
        fraud_score = round(random.uniform(0.0, 0.29), 4)
        amount = round(random.uniform(*LEGITIMATE_AMOUNT_RANGE), 2)
    elif fraud_type == "suspicious":
        fraud_score = round(random.uniform(0.3, 0.79), 4)
        amount = round(random.uniform(*SUSPICIOUS_AMOUNT_RANGE), 2)
    else:  # fraudulent
        fraud_score = round(random.uniform(0.8, 1.0), 4)
        amount = round(random.uniform(*FRAUDULENT_AMOUNT_RANGE), 2)

    # Generate timestamp (last 30 days)
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    timestamp = datetime.utcnow() - timedelta(
        days=days_ago, hours=hours_ago, minutes=minutes_ago
    )

    # Generate customer data
    email = generate_email(fraud_type)
    ip_address = generate_ip_address(fraud_type)

    # Generate card data
    card_data = generate_card_data()

    # Calculate risk level and decision
    risk_level = calculate_risk_level(fraud_score)
    decision = calculate_decision(risk_level, fraud_score)

    transaction = {
        "transaction_id": generate_transaction_id(),
        "amount": Decimal(str(amount)),
        "currency": "PEN",
        "timestamp": timestamp,
        # Customer data
        "customer_id": f"cust_{fake.uuid4()[:12]}",
        "customer_email": email,
        "customer_phone": fake.phone_number()[:15] if random.random() > 0.2 else None,
        "customer_ip": ip_address,
        # Payment method
        "card_bin": card_data["card_bin"],
        "card_last4": card_data["card_last4"],
        "card_brand": card_data["card_brand"],
        # Fraud detection
        "fraud_score": Decimal(str(fraud_score)),
        "risk_level": risk_level,
        "decision": decision,
    }

    return transaction


async def seed_transactions():
    """Seed database with test transactions

    Generates 1000 transactions with realistic data:
    - 800 legitimate (80%)
    - 150 suspicious (15%)
    - 50 fraudulent (5%)
    """
    logger.info("Starting transaction seeding process...")

    prisma = Prisma()

    try:
        await prisma.connect()
        logger.info("Connected to database")

        # Clear existing transactions (optional - comment out if you want to keep existing data)
        logger.info("Clearing existing transactions...")
        deleted_count = await prisma.transaction.delete_many()
        logger.info(f"Deleted {deleted_count} existing transactions")

        transactions = []

        # Generate legitimate transactions (800)
        logger.info(f"Generating {LEGITIMATE_COUNT} legitimate transactions...")
        for i in range(LEGITIMATE_COUNT):
            transaction = generate_transaction("legitimate", i)
            transactions.append(transaction)

        # Generate suspicious transactions (150)
        logger.info(f"Generating {SUSPICIOUS_COUNT} suspicious transactions...")
        for i in range(SUSPICIOUS_COUNT):
            transaction = generate_transaction("suspicious", i)
            transactions.append(transaction)

        # Generate fraudulent transactions (50)
        logger.info(f"Generating {FRAUDULENT_COUNT} fraudulent transactions...")
        for i in range(FRAUDULENT_COUNT):
            transaction = generate_transaction("fraudulent", i)
            transactions.append(transaction)

        # Shuffle to mix transaction types
        random.shuffle(transactions)

        # Insert transactions in batches
        batch_size = 100
        total_inserted = 0

        logger.info(
            f"Inserting {len(transactions)} transactions in batches of {batch_size}..."
        )

        for i in range(0, len(transactions), batch_size):
            batch = transactions[i : i + batch_size]

            for transaction in batch:
                await prisma.transaction.create(data=transaction)
                total_inserted += 1

            logger.info(
                f"Inserted {total_inserted}/{len(transactions)} transactions..."
            )

        logger.info(f"✅ Successfully seeded {total_inserted} transactions!")

        # Print statistics
        stats = {
            "LOW": await prisma.transaction.count(where={"risk_level": RISK_LEVEL_LOW}),
            "MEDIUM": await prisma.transaction.count(
                where={"risk_level": RISK_LEVEL_MEDIUM}
            ),
            "HIGH": await prisma.transaction.count(
                where={"risk_level": RISK_LEVEL_HIGH}
            ),
            "CRITICAL": await prisma.transaction.count(
                where={"risk_level": RISK_LEVEL_CRITICAL}
            ),
        }

        logger.info("\n📊 Transaction Statistics:")
        logger.info(f"  - LOW risk: {stats['LOW']}")
        logger.info(f"  - MEDIUM risk: {stats['MEDIUM']}")
        logger.info(f"  - HIGH risk: {stats['HIGH']}")
        logger.info(f"  - CRITICAL risk: {stats['CRITICAL']}")

        decision_stats = {
            "APPROVE": await prisma.transaction.count(
                where={"decision": DECISION_APPROVE}
            ),
            "REVIEW": await prisma.transaction.count(
                where={"decision": DECISION_REVIEW}
            ),
            "DECLINE": await prisma.transaction.count(
                where={"decision": DECISION_DECLINE}
            ),
        }

        logger.info("\n📋 Decision Statistics:")
        logger.info(f"  - APPROVE: {decision_stats['APPROVE']}")
        logger.info(f"  - REVIEW: {decision_stats['REVIEW']}")
        logger.info(f"  - DECLINE: {decision_stats['DECLINE']}")

    except Exception as e:
        logger.error(f"❌ Error seeding transactions: {str(e)}", exc_info=True)
        raise

    finally:
        await prisma.disconnect()
        logger.info("Disconnected from database")


if __name__ == "__main__":
    asyncio.run(seed_transactions())
