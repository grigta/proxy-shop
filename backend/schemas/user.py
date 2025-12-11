"""User Profile & Referral API schemas"""

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.models.user import PlatformType


class UserProfileResponse(BaseModel):
    """
    Response schema for GET /user/profile endpoint.
    Returns complete user profile information including balance, referral data, and statistics.
    """

    user_id: int = Field(..., description="Unique user identifier (Acc Id)")
    access_code: str = Field(..., description="User's access code for authentication")
    balance: Decimal = Field(..., description="Current account balance in USD (may be from forwarded account if balance_forward is set)")
    datestamp: datetime = Field(..., description="Registration date (Reg date)")
    platform_registered: PlatformType = Field(..., description="Platform where user registered")
    language: str = Field(..., description="User interface language preference")
    username: Optional[str] = Field(None, description="Username if set")
    telegram_id: Optional[List[int]] = Field(None, description="List of linked Telegram IDs, first element is the account owner")
    telegram_id_owner: Optional[int] = Field(None, description="Telegram ID of the account owner (first element of telegram_id)")
    linked_telegram_ids: List[int] = Field(default_factory=list, description="Additional linked Telegram IDs (excluding the owner)")
    balance_forward: Optional[int] = Field(None, description="User ID whose balance is used if set")

    # Referral information
    referral_link_bot: str = Field(..., description="Referral link for Telegram bot")
    referral_link_web: str = Field(..., description="Referral link for web interface")
    myreferal_id: Optional[str] = Field(None, description="User's referral code")
    referal_quantity: int = Field(..., description="Number of referred users (Referrals)")
    total_earned_from_referrals: Decimal = Field(..., description="Total amount earned from referral bonuses")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 123,
                "access_code": "1234",
                "balance": "100.50",
                "datestamp": "2025-01-15T10:30:00",
                "platform_registered": "BOT",
                "language": "en",
                "username": "john_doe",
                "telegram_id": [123456789, 987654321],
                "telegram_id_owner": 123456789,
                "linked_telegram_ids": [987654321],
                "balance_forward": None,
                "referral_link_bot": "http://t.me/proxy_shop_bot?start=ref_ABCDEFGH2",
                "referral_link_web": "https://proxy-shop.com/register?ref=ref_ABCDEFGH2",
                "myreferal_id": "ref_ABCDEFGH2",
                "referal_quantity": 5,
                "total_earned_from_referrals": "25.50"
            }
        }
    )


class UserHistoryItem(BaseModel):
    """
    Model for a single user history entry.
    Represents an action from the user_logs table with formatted message.
    """

    id_log: int = Field(..., description="Unique log entry identifier")
    action_type: str = Field(..., description="Type of action (DEPOSIT, BUY_SOCKS5, BUY_PPTP, REFUND, etc.)")
    action_description: str = Field(..., description="Detailed description of the action")
    date_of_action: datetime = Field(..., description="Date and time when action occurred")
    formatted_message: str = Field(..., description="User-friendly formatted message for display")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id_log": 1001,
                "action_type": "DEPOSIT",
                "action_description": "Deposit of 9.932 USD via USDT TRC20",
                "date_of_action": "2025-10-24T21:14:01",
                "formatted_message": "DEPOSIT AMOUNT 9.932 🕞2025-10-24 21:14:01 UTC0"
            }
        }
    )


class UserHistoryResponse(BaseModel):
    """
    Response schema for GET /user/history endpoint.
    Returns paginated user action history from logs.
    """

    history: List[UserHistoryItem] = Field(..., description="List of user history entries")
    total: int = Field(..., description="Total number of history entries")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "history": [
                    {
                        "id_log": 1001,
                        "action_type": "DEPOSIT",
                        "action_description": "Deposit of 9.932 USD via USDT TRC20",
                        "date_of_action": "2025-10-24T21:14:01",
                        "formatted_message": "DEPOSIT AMOUNT 9.932 🕞2025-10-24 21:14:01 UTC0"
                    },
                    {
                        "id_log": 1002,
                        "action_type": "BUY_SOCKS5",
                        "action_description": "Purchased SOCKS5 proxy for 2.00 USD",
                        "date_of_action": "2025-10-24T21:15:30",
                        "formatted_message": "BUY Socks5 2.00 🕞2025-10-24 21:15:30 UTC0"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20
            }
        }
    )


class ReferralItem(BaseModel):
    """
    Model for a single referral user.
    Contains referral statistics and earned bonus information.
    """

    user_id: int = Field(..., description="Referral's user ID")
    username: Optional[str] = Field(None, description="Referral's username if set")
    datestamp: datetime = Field(..., description="Referral's registration date")
    total_spent: Decimal = Field(..., description="Total amount spent by this referral")
    bonus_earned: Decimal = Field(..., description="Bonus earned from this referral's purchases")
    is_active: bool = Field(..., description="Whether referral has made any purchases")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 456,
                "username": "referred_user",
                "datestamp": "2025-01-20T15:45:00",
                "total_spent": "50.00",
                "bonus_earned": "5.00",
                "is_active": True
            }
        }
    )


class ReferralsResponse(BaseModel):
    """
    Response schema for GET /user/referrals/{user_id} endpoint.
    Returns user's referrals list with statistics.
    """

    referrals: List[ReferralItem] = Field(..., description="List of referred users")
    total_referrals: int = Field(..., description="Total number of referrals")
    total_earned: Decimal = Field(..., description="Total amount earned from all referrals")
    referral_bonus_percentage: int = Field(..., description="Current referral bonus percentage")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "referrals": [
                    {
                        "user_id": 456,
                        "username": "referred_user1",
                        "datestamp": "2025-01-20T15:45:00",
                        "total_spent": "50.00",
                        "bonus_earned": "5.00",
                        "is_active": True
                    },
                    {
                        "user_id": 457,
                        "username": None,
                        "datestamp": "2025-01-21T10:30:00",
                        "total_spent": "0.00",
                        "bonus_earned": "0.00",
                        "is_active": False
                    }
                ],
                "total_referrals": 10,
                "total_earned": "25.50",
                "referral_bonus_percentage": 10,
                "page": 1,
                "page_size": 20
            }
        }
    )


class ActivateCouponRequest(BaseModel):
    """
    Request schema for POST /user/coupon/activate endpoint.
    Used to activate a discount coupon for future purchases.
    """

    coupon_code: str = Field(..., min_length=1, max_length=50, description="Discount coupon code to activate")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "coupon_code": "DISCOUNT10"
            }
        }
    )


class ActivateCouponResponse(BaseModel):
    """
    Response schema for successful coupon activation.
    Returns coupon details and discount information.
    """

    success: bool = Field(..., description="Whether activation was successful")
    message: str = Field(..., description="User-friendly message about activation")
    coupon_code: str = Field(..., description="Activated coupon code")
    discount_percentage: Decimal = Field(..., description="Discount percentage (0-100)")
    discount_amount: Optional[Decimal] = Field(None, description="Discount amount if applied immediately")
    expires_at: Optional[datetime] = Field(None, description="Coupon expiration date if set")
    usage_info: str = Field(..., description="Information about coupon usage limits")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Coupon activated successfully",
                "coupon_code": "DISCOUNT10",
                "discount_percentage": "10.00",
                "discount_amount": None,
                "expires_at": "2025-12-31T23:59:59",
                "usage_info": "Used 5 of 100 times"
            }
        }
    )


class LinkByKeyRequest(BaseModel):
    """
    Request schema for POST /user/link-by-key endpoint.
    Used to link Telegram account to existing user by access code.
    """

    access_code: str = Field(..., min_length=11, max_length=11, description="Access code in format XXX-XXX-XXX")
    telegram_id: int = Field(..., gt=0, description="Telegram user ID to link")
    username: Optional[str] = Field(None, max_length=255, description="Telegram username")

    @classmethod
    def normalize_access_code(cls, v: str) -> str:
        """Normalize access code to uppercase"""
        return v.strip().upper() if v else v

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "access_code": "ABC-123-XYZ",
                "telegram_id": 123456789,
                "username": "johndoe"
            }
        }
    )


class LinkByKeyResponse(BaseModel):
    """
    Response schema for successful link-by-key operation.
    Returns new JWT tokens and updated user information.
    """

    success: bool = Field(..., description="Whether linking was successful")
    message: str = Field(..., description="User-friendly message about linking")
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    user_id: int = Field(..., description="User ID")
    telegram_id: List[int] = Field(..., description="Updated list of linked Telegram IDs")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Telegram account linked successfully",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user_id": 123,
                "telegram_id": [123456789]
            }
        }
    )


class ManageLinkedUserRequest(BaseModel):
    """
    Request schema for POST /user/linked-users/add and /user/linked-users/remove endpoints.
    Used to add or remove Telegram ID from linked users list.
    """

    telegram_id: int = Field(..., gt=0, description="Telegram ID to add or remove")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "telegram_id": 987654321
            }
        }
    )


class ManageLinkedUserResponse(BaseModel):
    """
    Response schema for linked user management operations.
    Returns updated list of linked users.
    """

    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="User-friendly message about operation")
    linked_telegram_ids: List[int] = Field(..., description="Updated list of linked Telegram IDs (excluding owner)")
    total: int = Field(..., description="Total number of linked users")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Telegram user added successfully",
                "linked_telegram_ids": [987654321, 111222333],
                "total": 2
            }
        }
    )


class LinkedUsersResponse(BaseModel):
    """
    Response schema for GET /user/linked-users endpoint.
    Returns list of Telegram IDs linked to current user's account.
    """

    telegram_id_owner: Optional[int] = Field(None, description="Telegram ID of account owner (first element), None if no Telegram ID is configured")
    linked_telegram_ids: List[int] = Field(default_factory=list, description="Additional linked Telegram IDs (excluding owner)")
    total: int = Field(..., description="Total number of linked users")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "telegram_id_owner": 123456789,
                "linked_telegram_ids": [987654321, 111222333],
                "total": 2
            }
        }
    )