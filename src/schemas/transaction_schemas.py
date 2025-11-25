"""
Transaction DTOs with Pydantic validation.
Implements request/response models with custom validators for DYGSOM Fraud API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


# Constants for validation
MIN_TRANSACTION_AMOUNT = 1.00
MAX_TRANSACTION_AMOUNT = 1_000_000.00
DEFAULT_CURRENCY = "PEN"


class CustomerData(BaseModel):
    """Customer information for transaction

    Validates customer data including email format, phone number, and IP address.
    """

    id: Optional[str] = Field(None, description="Customer unique identifier")
    email: str = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, description="Customer phone number")
    ip_address: str = Field(..., description="Customer IP address")
    device_fingerprint: Optional[str] = Field(
        None, description="Device fingerprint for fraud detection"
    )

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Validate email format

        Args:
            v: Email string

        Returns:
            Validated email in lowercase

        Raises:
            ValueError: If email format is invalid
        """
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @validator("ip_address")
    def validate_ip_address(cls, v: str) -> str:
        """Validate IP address format (IPv4)

        Args:
            v: IP address string

        Returns:
            Validated IP address

        Raises:
            ValueError: If IP format is invalid or is private IP
        """
        # IPv4 pattern
        ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
        match = re.match(ipv4_pattern, v)

        if not match:
            raise ValueError("Invalid IP address format (must be IPv4)")

        # Validate each octet is 0-255
        octets = [int(match.group(i)) for i in range(1, 5)]
        if any(octet > 255 for octet in octets):
            raise ValueError("Invalid IP address (octets must be 0-255)")

        # Reject private IP addresses (for production use)
        first_octet = octets[0]
        second_octet = octets[1]

        # 10.0.0.0/8
        if first_octet == 10:
            raise ValueError("Private IP addresses not allowed (10.x.x.x)")

        # 172.16.0.0/12
        if first_octet == 172 and 16 <= second_octet <= 31:
            raise ValueError("Private IP addresses not allowed (172.16-31.x.x)")

        # 192.168.0.0/16
        if first_octet == 192 and second_octet == 168:
            raise ValueError("Private IP addresses not allowed (192.168.x.x)")

        # 127.0.0.0/8 (localhost)
        if first_octet == 127:
            raise ValueError("Localhost IP not allowed")

        return v

    @validator("phone")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format

        Args:
            v: Phone number string

        Returns:
            Validated phone number (digits only)

        Raises:
            ValueError: If phone format is invalid
        """
        if v is None:
            return v

        # Remove common separators
        phone_digits = re.sub(r"[\s\-\(\)\+]", "", v)

        # Check if only digits remain
        if not phone_digits.isdigit():
            raise ValueError("Phone number must contain only digits")

        # Check length (8-15 digits is reasonable for international)
        if len(phone_digits) < 8 or len(phone_digits) > 15:
            raise ValueError("Phone number must be 8-15 digits")

        return phone_digits

    class Config:
        schema_extra = {
            "example": {
                "id": "cust_123456",
                "email": "juan.perez@gmail.com",
                "phone": "+51987654321",
                "ip_address": "181.67.45.123",
                "device_fingerprint": "fp_abc123xyz",
            }
        }


class PaymentMethodData(BaseModel):
    """Payment method information for transaction

    Validates payment method details including card BIN and last 4 digits.
    """

    type: str = Field(
        ..., description="Payment method type (credit_card or debit_card)"
    )
    bin: str = Field(
        ..., min_length=6, max_length=6, description="Card BIN (first 6 digits)"
    )
    last4: str = Field(
        ..., min_length=4, max_length=4, description="Card last 4 digits"
    )
    brand: str = Field(..., description="Card brand (Visa, Mastercard, Amex, etc.)")

    @validator("type")
    def validate_payment_type(cls, v: str) -> str:
        """Validate payment method type

        Args:
            v: Payment type string

        Returns:
            Validated payment type in lowercase

        Raises:
            ValueError: If payment type is not supported
        """
        allowed_types = ["credit_card", "debit_card"]
        v_lower = v.lower()

        if v_lower not in allowed_types:
            raise ValueError(f"Payment type must be one of: {', '.join(allowed_types)}")

        return v_lower

    @validator("bin")
    def validate_bin(cls, v: str) -> str:
        """Validate card BIN format

        Args:
            v: BIN string

        Returns:
            Validated BIN

        Raises:
            ValueError: If BIN format is invalid
        """
        if not v.isdigit():
            raise ValueError("Card BIN must contain only digits")

        if len(v) != 6:
            raise ValueError("Card BIN must be exactly 6 digits")

        return v

    @validator("last4")
    def validate_last4(cls, v: str) -> str:
        """Validate card last 4 digits format

        Args:
            v: Last 4 digits string

        Returns:
            Validated last 4 digits

        Raises:
            ValueError: If format is invalid
        """
        if not v.isdigit():
            raise ValueError("Card last 4 must contain only digits")

        if len(v) != 4:
            raise ValueError("Card last 4 must be exactly 4 digits")

        return v

    @validator("brand")
    def validate_brand(cls, v: str) -> str:
        """Validate card brand

        Args:
            v: Card brand string

        Returns:
            Validated brand in title case

        Raises:
            ValueError: If brand is not recognized
        """
        allowed_brands = ["visa", "mastercard", "amex", "discover", "diners", "jcb"]
        v_lower = v.lower()

        if v_lower not in allowed_brands:
            raise ValueError(f"Card brand must be one of: {', '.join(allowed_brands)}")

        # Return in title case
        return v_lower.title()

    class Config:
        schema_extra = {
            "example": {
                "type": "credit_card",
                "bin": "411111",
                "last4": "1111",
                "brand": "Visa",
            }
        }


class CreateTransactionDto(BaseModel):
    """DTO for creating a new transaction

    Validates all transaction data including amount limits and currency.
    """

    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(
        default=DEFAULT_CURRENCY, description="Currency code (ISO 4217)"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Transaction timestamp (defaults to now)"
    )

    customer: CustomerData = Field(..., description="Customer information")
    payment_method: PaymentMethodData = Field(
        ..., description="Payment method information"
    )

    @validator("transaction_id")
    def validate_transaction_id(cls, v: str) -> str:
        """Validate transaction ID format

        Args:
            v: Transaction ID string

        Returns:
            Validated transaction ID

        Raises:
            ValueError: If transaction ID format is invalid
        """
        if not v or len(v.strip()) == 0:
            raise ValueError("Transaction ID cannot be empty")

        # Must be alphanumeric with optional underscores/hyphens
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Transaction ID must be alphanumeric (with _ or - allowed)"
            )

        if len(v) < 3 or len(v) > 100:
            raise ValueError("Transaction ID must be 3-100 characters")

        return v

    @validator("amount")
    def validate_amount(cls, v: float) -> float:
        """Validate transaction amount

        Args:
            v: Amount value

        Returns:
            Validated amount

        Raises:
            ValueError: If amount is outside allowed range
        """
        if v <= 0:
            raise ValueError("Amount must be positive")

        if v < MIN_TRANSACTION_AMOUNT:
            raise ValueError(f"Amount must be at least {MIN_TRANSACTION_AMOUNT} PEN")

        if v > MAX_TRANSACTION_AMOUNT:
            raise ValueError(f"Amount cannot exceed {MAX_TRANSACTION_AMOUNT:,.2f} PEN")

        # Round to 2 decimal places
        return round(v, 2)

    @validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code

        Args:
            v: Currency code string

        Returns:
            Validated currency code in uppercase

        Raises:
            ValueError: If currency code is invalid
        """
        # Must be 3 uppercase letters (ISO 4217)
        v_upper = v.upper()

        if not re.match(r"^[A-Z]{3}$", v_upper):
            raise ValueError("Currency must be a 3-letter ISO code (e.g., PEN, USD)")

        # For now, only support PEN (can be extended later)
        supported_currencies = ["PEN", "USD"]
        if v_upper not in supported_currencies:
            raise ValueError(
                f"Currency must be one of: {', '.join(supported_currencies)}"
            )

        return v_upper

    @validator("timestamp", always=True)
    def set_timestamp(cls, v: Optional[datetime]) -> datetime:
        """Set timestamp to now if not provided

        Args:
            v: Timestamp value

        Returns:
            Timestamp (now if None)
        """
        return v or datetime.utcnow()

    class Config:
        schema_extra = {
            "example": {
                "transaction_id": "txn_abc123xyz789",
                "amount": 150.50,
                "currency": "PEN",
                "timestamp": "2024-11-24T10:30:00Z",
                "customer": {
                    "id": "cust_123456",
                    "email": "juan.perez@gmail.com",
                    "phone": "+51987654321",
                    "ip_address": "181.67.45.123",
                    "device_fingerprint": "fp_abc123xyz",
                },
                "payment_method": {
                    "type": "credit_card",
                    "bin": "411111",
                    "last4": "1111",
                    "brand": "Visa",
                },
            }
        }


class TransactionResponseDto(BaseModel):
    """DTO for transaction response

    Returns transaction data with fraud scoring results.
    """

    id: str = Field(..., description="Internal transaction ID (UUID)")
    transaction_id: str = Field(..., description="Business transaction identifier")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Currency code")

    customer_email: str = Field(..., description="Customer email")
    customer_ip: str = Field(..., description="Customer IP address")

    card_bin: str = Field(..., description="Card BIN")
    card_last4: str = Field(..., description="Card last 4 digits")
    card_brand: str = Field(..., description="Card brand")

    fraud_score: Optional[float] = Field(
        None, description="Fraud probability score (0-1)"
    )
    risk_level: Optional[str] = Field(
        None, description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)"
    )
    decision: Optional[str] = Field(
        None, description="Decision (APPROVE, REVIEW, DECLINE)"
    )

    timestamp: datetime = Field(..., description="Transaction timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "transaction_id": "txn_abc123xyz789",
                "amount": 150.50,
                "currency": "PEN",
                "customer_email": "juan.perez@gmail.com",
                "customer_ip": "181.67.45.123",
                "card_bin": "411111",
                "card_last4": "1111",
                "card_brand": "Visa",
                "fraud_score": 0.15,
                "risk_level": "LOW",
                "decision": "APPROVE",
                "timestamp": "2024-11-24T10:30:00Z",
                "created_at": "2024-11-24T10:30:01Z",
            }
        }
