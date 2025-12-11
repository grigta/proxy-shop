from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_client_ip, get_current_user
from backend.core.database import get_async_session
from backend.core.security import decode_refresh_token, get_token_expiry
from backend.models.user import User
from backend.schemas.auth import (
    LinkTelegramRequest,
    LinkTelegramResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    TelegramAuthRequest,
    TelegramAuthResponse,
    TokenVerifyResponse
)
from backend.services.auth_service import AuthService

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and receive access tokens"
)
async def register(
    request_data: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Register a new user in the system.

    Returns access code and JWT tokens for authentication.
    """
    try:

        # Register user
        user, access_token, refresh_token = await AuthService.register_user(
            session,
            platform=request_data.platform.value,
            language=request_data.language,
            telegram_id=request_data.telegram_id,
            username=request_data.username,
            referral_code=request_data.referral_code,
            ip=client_ip
        )

        return RegisterResponse(
            access_code=user.access_code,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.user_id,
            platform=user.platform_registered
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.post(
    "/telegram-auth",
    response_model=TelegramAuthResponse,
    summary="Authenticate via Telegram",
    description="Authenticate or register user using Telegram ID. Returns access code and tokens. Works for both new and existing users."
)
async def telegram_auth(
    request_data: TelegramAuthRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Authenticate or register user using Telegram ID.

    For existing users: Returns existing access code and new tokens.
    For new users: Creates account, returns new access code and tokens.
    """
    try:
        # Authenticate or register user
        user, access_token, refresh_token, is_new_user = await AuthService.authenticate_telegram_user(
            session,
            telegram_id=request_data.telegram_id,
            username=request_data.username,
            language=request_data.language,
            referral_code=request_data.referral_code,
            ip=client_ip
        )

        response_status = status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK

        return TelegramAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.user_id,
            access_code=user.access_code,
            is_new_user=is_new_user,
            platform_registered=user.platform_registered,
            balance=user.balance
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate via Telegram: {str(e)}"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with access code",
    description="Authenticate using access code and receive JWT tokens"
)
async def login(
    request_data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Authenticate user with access code.

    Returns JWT tokens and user information.
    """
    # Get user agent from headers
    user_agent = request.headers.get("user-agent")

    try:
        # Authenticate user
        user, access_token, refresh_token = await AuthService.login_user(
            session,
            access_code=request_data.access_code,
            ip=client_ip,
            user_agent=user_agent
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.user_id,
            access_code=user.access_code,
            platform_registered=user.platform_registered,
            balance=user.balance,
            telegram_id=user.telegram_id,
            is_admin=user.is_admin
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/verify",
    response_model=TokenVerifyResponse,
    summary="Verify access token",
    description="Check if the provided access token is valid"
)
async def verify_token(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verify the validity of an access token.

    Returns user information if token is valid.
    """
    # Extract expiry from token if available
    expires_at = None
    if hasattr(current_user, 'access_token'):
        expires_at = get_token_expiry(current_user.access_token)  # type: ignore

    return TokenVerifyResponse(
        valid=True,
        user_id=current_user.user_id,
        access_code=current_user.access_code,
        expires_at=expires_at
    )


@router.post(
    "/link-telegram",
    response_model=LinkTelegramResponse,
    summary="Link Telegram account",
    description="Link a Telegram account to existing user"
)
async def link_telegram(
    request_data: LinkTelegramRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Link Telegram account to current authenticated user.

    Requires valid access token.
    """
    try:
        # Link Telegram account
        user = await AuthService.link_telegram_to_user(
            session,
            user_id=current_user.user_id,
            telegram_id=request_data.telegram_id,
            username=request_data.username,
            ip=client_ip
        )

        return LinkTelegramResponse(
            success=True,
            message="Telegram account linked successfully",
            telegram_id=user.telegram_id,
            access_code=user.access_code
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link Telegram account: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Get a new access token using refresh token"
)
async def refresh_token(
    request_data: RefreshTokenRequest,
    request: Request = None,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Refresh access token using a valid refresh token.

    Returns new access token.
    """
    # Decode refresh token
    user_id = decode_refresh_token(request_data.refresh_token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        # Generate new access token
        access_token = await AuthService.refresh_access_token(
            session,
            user_id=user_id,
            ip=client_ip
        )

        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}"
        )