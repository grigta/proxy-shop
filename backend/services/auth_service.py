from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token, create_refresh_token
from backend.models.user import User
from backend.scripts.generate_access_code import generate_unique_access_code
from backend.services.log_service import LogService


class AuthService:
    """Service for authentication and user management business logic"""

    @staticmethod
    async def register_user(
        session: AsyncSession,
        platform: str,
        language: str = "ru",
        telegram_id: Optional[int] = None,
        username: Optional[str] = None,
        referral_code: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Register a new user in the system.

        Args:
            session: Database session
            platform: Registration platform (telegram/web)
            language: User interface language
            telegram_id: Optional Telegram ID if registering via bot
            username: Optional username
            referral_code: Optional referral code
            ip: Client IP address

        Returns:
            Tuple of (User object, access_token, refresh_token)
        """
        # Check if telegram_id is already linked to another user
        if telegram_id:
            result = await session.execute(
                select(User).where(User.telegram_id.contains([telegram_id]))
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="This Telegram account is already linked to another user"
                )

        # Generate unique access code
        access_code = await generate_unique_access_code(session)

        # Find referrer if referral code provided
        referrer = None
        if referral_code:
            result = await session.execute(
                select(User).where(User.myreferal_id.contains([referral_code]))
            )
            referrer = result.scalar_one_or_none()

        # Create new user
        user = User(
            access_code=access_code,
            platform_registered=platform,
            language=language,
            telegram_id=[telegram_id] if telegram_id else None,
            username=username,
            user_referal_id=referrer.user_id if referrer else None,
            myreferal_id=[f"ref_{access_code.replace('-', '')}"],
            balance=Decimal('0.00'),
            referal_quantity=0,
            balance_forward=None
        )

        # Add user to session
        session.add(user)
        await session.flush()  # Get user_id before commit

        # Update referrer's referral count
        if referrer:
            referrer.referal_quantity += 1

        # Create JWT tokens
        access_token = create_access_token({"sub": str(user.user_id)})
        refresh_token = create_refresh_token({"sub": str(user.user_id)})

        # Log registration
        await LogService.log_register(
            session,
            user.user_id,
            platform,
            user.access_code,
            ip
        )

        # Commit transaction
        await session.commit()
        await session.refresh(user)

        return user, access_token, refresh_token

    @staticmethod
    async def login_user(
        session: AsyncSession,
        access_code: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticate user by access code.

        Args:
            session: Database session
            access_code: User's access code (case-insensitive)
            ip: Client IP address
            user_agent: Client user agent string

        Returns:
            Tuple of (User object, access_token, refresh_token)

        Raises:
            HTTPException: If access code is invalid
        """
        # Normalize access code to uppercase for case-insensitive comparison
        access_code = access_code.upper()
        
        # Find user by access code
        result = await session.execute(
            select(User).where(User.access_code == access_code)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid access code"
            )

        # Create JWT tokens
        access_token = create_access_token({"sub": str(user.user_id)})
        refresh_token = create_refresh_token({"sub": str(user.user_id)})

        # Log login
        await LogService.log_login(
            session,
            user.user_id,
            user.platform_registered.value,
            access_code,
            ip,
            user_agent
        )

        await session.commit()

        return user, access_token, refresh_token

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession,
        user_id: int
    ) -> Optional[User]:
        """
        Get user by their ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def link_telegram_to_user(
        session: AsyncSession,
        user_id: int,
        telegram_id: int,
        username: Optional[str] = None,
        ip: Optional[str] = None
    ) -> User:
        """
        Link Telegram account to existing user.

        Args:
            session: Database session
            user_id: User ID to link Telegram to
            telegram_id: Telegram ID to link
            username: Optional Telegram username
            ip: Client IP address

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found or Telegram already linked
        """
        # Find user by ID
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Check if Telegram ID is already linked to another user
        result = await session.execute(
            select(User).where(User.telegram_id.contains([telegram_id]))
        )
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.user_id != user_id:
            raise HTTPException(
                status_code=400,
                detail="This Telegram account is already linked to another user"
            )

        # Check if user already has linked Telegram
        if user.telegram_id and telegram_id in user.telegram_id:
            raise HTTPException(
                status_code=400,
                detail="This Telegram account is already linked to this user"
            )

        # Update user
        if user.telegram_id is None:
            user.telegram_id = [telegram_id]
        else:
            user.telegram_id = user.telegram_id + [telegram_id]
        user.username = username or user.username

        # Log the linking
        await LogService.log_link_telegram(
            session,
            user_id,
            telegram_id,
            user.access_code,
            ip
        )

        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def refresh_access_token(
        session: AsyncSession,
        user_id: int,
        ip: Optional[str] = None
    ) -> str:
        """
        Generate new access token for user.

        Args:
            session: Database session
            user_id: User ID
            ip: Client IP address

        Returns:
            New access token

        Raises:
            HTTPException: If user not found
        """
        # Verify user exists
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Create new access token
        access_token = create_access_token({"sub": str(user_id)})

        # Log token refresh
        await LogService.log_token_refresh(session, user_id, ip)

        await session.commit()

        return access_token

    @staticmethod
    async def authenticate_telegram_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        language: str = "ru",
        referral_code: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[User, str, str, bool]:
        """
        Authenticate or register user by Telegram ID.

        Args:
            session: Database session
            telegram_id: Telegram user ID
            username: Optional Telegram username
            language: User language preference
            referral_code: Optional referral code
            ip: Client IP address

        Returns:
            Tuple of (User object, access_token, refresh_token, is_new_user)
        """
        # Query database for existing user with this telegram_id
        result = await session.execute(
            select(User).where(User.telegram_id.contains([telegram_id]))
        )
        user = result.scalar_one_or_none()

        if user:
            # Validate that first telegram_id is the owner
            if user.telegram_id and user.telegram_id[0] != telegram_id:
                # This is not the owner account, but a linked user - deny access
                await LogService.log_login(
                    session,
                    user.user_id,
                    user.platform_registered.value,
                    user.access_code,
                    ip,
                    None  # user_agent
                )
                raise HTTPException(
                    status_code=403,
                    detail="Authentication denied. This Telegram ID is not the account owner."
                )

            # User exists - update username if provided and different
            if username and user.username != username:
                user.username = username

            # Generate new JWT tokens
            access_token = create_access_token({"sub": str(user.user_id)})
            refresh_token = create_refresh_token({"sub": str(user.user_id)})

            # Log login event
            await LogService.log_login(
                session,
                user.user_id,
                user.platform_registered.value,
                user.access_code,
                ip,
                None  # user_agent
            )

            await session.commit()
            await session.refresh(user)

            return user, access_token, refresh_token, False

        else:
            # User doesn't exist - register new user
            user, access_token, refresh_token = await AuthService.register_user(
                session,
                platform="telegram",
                language=language,
                telegram_id=telegram_id,
                username=username,
                referral_code=referral_code,
                ip=ip
            )

            return user, access_token, refresh_token, True