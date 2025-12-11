from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_async_session
from backend.core.security import decode_access_token
from backend.models.user import User
from backend.services.auth_service import AuthService

# Security scheme for Bearer token authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header
        session: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Extract token from credentials
    token = credentials.credentials

    # Decode token and get user_id
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user from database
    user = await AuthService.get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Store the token in the user object for later use (non-persistent)
    user.access_token = token  # type: ignore

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Optional dependency to get current user if authenticated.
    Returns None if no authentication provided or token is invalid.

    Args:
        credentials: Optional Bearer token from Authorization header
        session: Database session

    Returns:
        Current User object or None
    """
    if credentials is None:
        return None

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Decode token and get user_id
        user_id = decode_access_token(token)

        if user_id is None:
            return None

        # Get user from database
        user = await AuthService.get_user_by_id(session, user_id)
        return user

    except Exception:
        # Return None for any authentication errors
        return None


async def get_client_ip(request: Request) -> Optional[str]:
    """
    Dependency to extract client IP address from request.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address or None
    """
    # Check for forwarded IP headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to client host
    if request.client:
        return request.client.host

    return None


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency to get current authenticated user and verify admin privileges.
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session
        
    Returns:
        Current User object with admin privileges
        
    Raises:
        HTTPException: If token is invalid, user not found, or user is not admin
    """
    # Get current user
    user = await get_current_user(credentials, session)
    
    # Check if user is admin
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. You do not have sufficient privileges to access this resource."
        )
    
    # Check if user is blocked
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been blocked. Please contact administrator."
        )
    
    return user
