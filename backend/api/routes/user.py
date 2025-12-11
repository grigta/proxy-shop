"""User Profile & Referral API routes"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_async_session
from backend.models.user import User
from backend.models.environment_variable import EnvironmentVariable
from backend.schemas.user import (
    UserProfileResponse,
    UserHistoryItem,
    UserHistoryResponse,
    ReferralItem,
    ReferralsResponse,
    ActivateCouponRequest,
    ActivateCouponResponse,
    LinkByKeyRequest,
    LinkByKeyResponse,
    ManageLinkedUserRequest,
    ManageLinkedUserResponse,
    LinkedUsersResponse
)
from backend.services.user_service import UserService
from backend.services.coupon_service import CouponService
from backend.services.referral_service import ReferralService
from backend.api.dependencies import get_current_user, get_client_ip

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/user", tags=["User Profile"])


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get user profile",
    description="Get current user's profile with balance, referral info, and statistics"
)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> UserProfileResponse:
    """
    Get complete user profile information.

    Returns:
        - User ID, access code, balance, registration date
        - Platform registered on, language preference
        - Referral links (bot and web)
        - Number of referrals and total earned from them
    """
    try:
        profile_data = await UserService.get_user_profile(session, current_user.user_id)
        return UserProfileResponse(**profile_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )


@router.get(
    "/history",
    response_model=UserHistoryResponse,
    summary="Get user action history",
    description="Get user's action history from logs with pagination"
)
async def get_user_history(
    action_type: Optional[str] = Query(None, description="Filter by action type (DEPOSIT, BUY_SOCKS5, BUY_PPTP, REFUND, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> UserHistoryResponse:
    """
    Get user's action history with optional filtering and pagination.

    Available action types:
    - DEPOSIT: Deposit transactions
    - BUY_SOCKS5: SOCKS5 proxy purchases
    - BUY_PPTP: PPTP proxy purchases
    - REFUND: Refund transactions
    - EXTEND_PROXY: Proxy extensions
    - COUPON_ACTIVATION: Coupon activations
    - COUPON_APPLIED: Coupon applications to purchases
    - REFERRAL_BONUS: Referral bonus awards
    - LOGIN: Login events
    - REGISTER: Registration event

    Returns formatted history messages like:
    - "DEPOSIT AMOUNT 9.932 🕞2025-10-24 21:14:01 UTC0"
    - "BUY Socks5 2.00 🕞2025-10-24 21:15:30 UTC0"
    """
    try:
        logs, total = await UserService.get_user_history(
            session, current_user.user_id, action_type, page, page_size
        )

        # Convert logs to UserHistoryItem objects
        history_items = []
        for log in logs:
            item = UserHistoryItem(
                id_log=log["id_log"],
                action_type=log["action_type"],
                action_description=log["action_description"],
                date_of_action=log["date_of_action"],
                formatted_message=log["formatted_message"]
            )
            history_items.append(item)

        return UserHistoryResponse(
            history=history_items,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error fetching history for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user history"
        )


@router.post(
    "/coupon/activate",
    response_model=ActivateCouponResponse,
    summary="Activate coupon",
    description="Activate a discount coupon for future purchases"
)
async def activate_coupon(
    request_data: ActivateCouponRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
) -> ActivateCouponResponse:
    """
    Activate a discount coupon for the current user.

    The activated coupon can be used in future purchases by providing
    the coupon_code parameter in POST /purchase/socks5 or /purchase/pptp.

    Validations:
    - Coupon must exist and be active
    - Coupon must not be expired
    - Coupon usage limit must not be reached
    - User must not have already used this coupon (one-time use per user)

    Returns:
    - Success status and discount percentage
    - Expiration date if set
    - Usage information (e.g., "Used 5 of 100 times")
    """
    try:
        coupon = await CouponService.activate_coupon(
            session, current_user.user_id, request_data.coupon_code, client_ip
        )

        # Format usage info
        if coupon.max_usage is None:
            usage_info = "Unlimited usage"
        else:
            remaining = coupon.max_usage - coupon.usage_quantity
            usage_info = f"{remaining} uses remaining"

        return ActivateCouponResponse(
            success=True,
            message="Coupon activated successfully",
            coupon_code=coupon.coupon,
            discount_percentage=coupon.discount_percentage,
            expires_at=coupon.expires_at,
            usage_info=usage_info
        )

    except HTTPException as e:
        # Re-raise HTTPExceptions with specific error messages
        raise
    except Exception as e:
        logger.error(f"Error activating coupon for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate coupon"
        )


@router.get(
    "/referrals/{user_id}",
    response_model=ReferralsResponse,
    summary="Get user referrals",
    description="Get list of user's referrals with statistics"
)
async def get_user_referrals(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> ReferralsResponse:
    """
    Get list of user's referrals with detailed statistics.

    Security: Users can only view their own referrals.

    Returns:
    - List of referrals with registration date and total spent
    - Bonus earned from each referral
    - Whether each referral is active (has made purchases)
    - Total amount earned from all referrals
    - Current referral bonus percentage
    """
    try:
        # Check access - users can only view their own referrals
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own referrals."
            )

        # Get referrals data
        referrals_data, total, total_earned = await ReferralService.get_user_referrals(
            session, user_id, page, page_size
        )

        # Get referral bonus percentage from environment variables
        bonus_percentage_result = await session.execute(
            select(EnvironmentVariable).where(
                EnvironmentVariable.name == "REFERRAL_BONUS_PERCENTAGE"
            )
        )
        bonus_percentage_var = bonus_percentage_result.scalar_one_or_none()
        bonus_percentage = int(bonus_percentage_var.data if bonus_percentage_var else "10")

        # Convert to ReferralItem objects
        referrals = []
        for ref_data in referrals_data:
            referral = ReferralItem(
                user_id=ref_data["user_id"],
                username=ref_data["username"],
                datestamp=ref_data["datestamp"],
                total_spent=ref_data["total_spent"],
                bonus_earned=ref_data["bonus_earned"],
                is_active=ref_data["is_active"]
            )
            referrals.append(referral)

        return ReferralsResponse(
            referrals=referrals,
            total_referrals=total,
            total_earned=total_earned,
            referral_bonus_percentage=bonus_percentage,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching referrals for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referrals"
        )


@router.post(
    "/link-by-key",
    response_model=LinkByKeyResponse,
    summary="Link Telegram by access code",
    description="Link Telegram account to existing user by access code. Used when user registered on website first and wants to connect Telegram bot."
)
async def link_by_access_code(
    request_data: LinkByKeyRequest,
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
) -> LinkByKeyResponse:
    """
    Link Telegram account to user by access code.

    This endpoint is used when a user registered on the website first
    and wants to link their Telegram account to access the bot.

    Args:
        request_data: Access code and Telegram ID
        session: Database session
        client_ip: Client IP address for logging

    Returns:
        Success status, new JWT tokens, and updated user information

    Raises:
        HTTPException: 404 if access code not found, 400 if telegram_id already linked
    """
    try:
        # Link telegram account
        user, access_token, refresh_token = await UserService.link_telegram_by_access_code(
            session=session,
            access_code=request_data.access_code,
            telegram_id=request_data.telegram_id,
            username=request_data.username,
            ip=client_ip
        )

        return LinkByKeyResponse(
            success=True,
            message="Telegram account linked successfully",
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.user_id,
            telegram_id=user.telegram_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking telegram by access code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link Telegram account"
        )


@router.get(
    "/linked-users",
    response_model=LinkedUsersResponse,
    summary="Get linked Telegram users",
    description="Get list of Telegram IDs linked to current user's account for balance sharing."
)
async def get_linked_users(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> LinkedUsersResponse:
    """
    Get list of linked Telegram users.

    Returns the owner telegram_id and all additional linked telegram_ids
    that share the same balance.

    Returns:
        telegram_id_owner: First telegram_id (account owner)
        linked_telegram_ids: Additional telegram_ids (excluding owner)
        total: Count of linked users

    Raises:
        HTTPException: 404 if user not found
    """
    try:
        # Get linked users
        result = await UserService.get_linked_telegram_users(
            session=session,
            user_id=current_user.user_id
        )

        return LinkedUsersResponse(
            telegram_id_owner=result["telegram_id_owner"],
            linked_telegram_ids=result["linked_telegram_ids"],
            total=result["total"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting linked users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get linked users"
        )


@router.post(
    "/linked-users/add",
    response_model=ManageLinkedUserResponse,
    summary="Add linked Telegram user",
    description="Add Telegram ID to linked users list. The added user will see and use the owner's balance. Only account owner can add users."
)
async def add_linked_user(
    request_data: ManageLinkedUserRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> ManageLinkedUserResponse:
    """
    Add Telegram ID to user's linked list.

    The added telegram_id will be appended to the user's telegram_id array.
    If the telegram_id belongs to another user (as owner), that user's
    balance_forward will be set to point to this account.

    Args:
        request_data: Telegram ID to add
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success status, message, and updated list of linked users

    Raises:
        HTTPException: 403 if not owner, 400 if telegram_id already linked, 404 if not found
    """
    try:
        # Add linked user
        linked_telegram_ids = await UserService.add_linked_telegram_user(
            session=session,
            owner_user_id=current_user.user_id,
            telegram_id=request_data.telegram_id
        )

        return ManageLinkedUserResponse(
            success=True,
            message="Telegram user added successfully",
            linked_telegram_ids=linked_telegram_ids,
            total=len(linked_telegram_ids)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding linked user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add linked user"
        )


@router.post(
    "/linked-users/remove",
    response_model=ManageLinkedUserResponse,
    summary="Remove linked Telegram user",
    description="Remove Telegram ID from linked users list. The removed user's balance_forward will be reset. Only account owner can remove users."
)
async def remove_linked_user(
    request_data: ManageLinkedUserRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> ManageLinkedUserResponse:
    """
    Remove Telegram ID from user's linked list.

    The telegram_id will be removed from the user's telegram_id array.
    If the telegram_id belongs to another user (as owner), that user's
    balance_forward will be reset to None.

    Args:
        request_data: Telegram ID to remove
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success status, message, and updated list of linked users

    Raises:
        HTTPException: 403 if not owner, 400 if trying to remove owner, 404 if not found
    """
    try:
        # Remove linked user
        linked_telegram_ids = await UserService.remove_linked_telegram_user(
            session=session,
            owner_user_id=current_user.user_id,
            telegram_id=request_data.telegram_id
        )

        return ManageLinkedUserResponse(
            success=True,
            message="Telegram user removed successfully",
            linked_telegram_ids=linked_telegram_ids,
            total=len(linked_telegram_ids)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing linked user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove linked user"
        )