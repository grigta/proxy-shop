from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from backend.core.config import settings

# Password hashing context (for future use)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The payload data to encode (usually contains {"sub": user_id})
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Encode and return token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The payload data to encode (usually contains {"sub": user_id})
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    # Encode and return token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload

    except ExpiredSignatureError:
        # Token has expired
        return None
    except JWTError:
        # Invalid token
        return None


def decode_access_token(token: str) -> Optional[int]:
    """
    Decode an access token and extract user_id.

    Args:
        token: The JWT access token

    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token, "access")
    if payload:
        try:
            user_id = int(payload.get("sub"))
            return user_id
        except (TypeError, ValueError):
            return None
    return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Extract expiry datetime from a JWT token.

    Args:
        token: The JWT token

    Returns:
        Expiry datetime if token is valid, None otherwise
    """
    try:
        # Decode token without verification to get expiry
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp)
    except JWTError:
        pass
    return None


def decode_refresh_token(token: str) -> Optional[int]:
    """
    Decode a refresh token and extract user_id.

    Args:
        token: The JWT refresh token

    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token, "refresh")
    if payload:
        try:
            user_id = int(payload.get("sub"))
            return user_id
        except (TypeError, ValueError):
            return None
    return None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    For future use when email/password authentication is added.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    For future use when email/password authentication is added.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)