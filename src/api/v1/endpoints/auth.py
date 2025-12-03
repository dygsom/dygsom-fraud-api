"""
Authentication endpoints for dashboard users.
Handles user signup, login, and session management with JWT tokens.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
import logging
import secrets

from src.core.config import settings
from src.dependencies import get_prisma, get_current_user
from prisma import Prisma

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# Request/Response Models
class SignupRequest(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=1)
    organization_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    name: Optional[str]
    role: str
    organization: Optional[dict]


# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash password with bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

    return encoded_jwt


def generate_api_key() -> str:
    """Generate a secure API key

    Returns:
        API key in format: dygsom_<32_chars>
    """
    random_part = secrets.token_urlsafe(32)[:32]
    return f"{settings.API_KEY_PREFIX}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage

    Args:
        api_key: Plain API key

    Returns:
        SHA-256 hash of API key
    """
    import hashlib
    return hashlib.sha256(f"{api_key}{settings.API_KEY_SALT}".encode()).hexdigest()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    prisma: Prisma = Depends(get_prisma)
):
    """
    Sign up new user and organization.

    Creates:
    1. New organization with startup plan
    2. New user (admin role)
    3. First API key (auto-generated)

    Args:
        request: Signup request with email, password, name, organization_name
        prisma: Prisma database client

    Returns:
        JWT access token and user information

    Raises:
        HTTPException 400: If email already registered
        HTTPException 500: If signup process fails
    """
    try:
        # Check if user already exists
        existing_user = await prisma.user.find_unique(
            where={"email": request.email}
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        logger.info(f"Creating new organization: {request.organization_name}")

        # Create organization
        organization = await prisma.organization.create(
            data={
                "name": request.organization_name,
                "plan": "startup"
            }
        )

        logger.info(f"Organization created: {organization.id}")

        # Hash password
        password_hash = hash_password(request.password)

        # Create user
        user = await prisma.user.create(
            data={
                "email": request.email,
                "password_hash": password_hash,
                "name": request.name,
                "organization_id": organization.id,
                "role": "admin"
            }
        )

        logger.info(f"User created: {user.id}")

        # Create first API key
        api_key_plain = generate_api_key()
        api_key_hash = hash_api_key(api_key_plain)

        await prisma.apikey.create(
            data={
                "key_hash": api_key_hash,
                "name": "Default API Key",
                "description": "Auto-generated key on signup",
                "organization_id": organization.id,
                "rate_limit": 1000,
                "created_by": user.id
            }
        )

        logger.info(f"API key created for organization: {organization.id}")

        # Create access token
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "organization_id": organization.id,
                "role": user.role
            }
        )

        return TokenResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "plan": organization.plan
                },
                "first_api_key": api_key_plain  # Return API key only once
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    prisma: Prisma = Depends(get_prisma)
):
    """
    Login user and return JWT token.

    Args:
        request: Login request with email and password
        prisma: Prisma database client

    Returns:
        JWT access token and user information

    Raises:
        HTTPException 401: If email or password is invalid
    """
    try:
        # Find user with organization
        user = await prisma.user.find_unique(
            where={"email": request.email},
            include={"organization": True}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update last login
        await prisma.user.update(
            where={"id": user.id},
            data={"last_login_at": datetime.utcnow()}
        )

        logger.info(f"User logged in: {user.email}")

        # Create access token
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "organization_id": user.organization_id,
                "role": user.role
            }
        )

        return TokenResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "organization": {
                    "id": user.organization.id,
                    "name": user.organization.name,
                    "plan": user.organization.plan
                } if user.organization else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    prisma: Prisma = Depends(get_prisma)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token
        prisma: Prisma database client

    Returns:
        User information with organization

    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 404: If user not found
    """

    try:
        user = await prisma.user.find_unique(
            where={"id": current_user["user_id"]},
            include={"organization": True}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            organization={
                "id": user.organization.id,
                "name": user.organization.name,
                "plan": user.organization.plan
            } if user.organization else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
