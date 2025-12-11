from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.models.user import PlatformType


class RegisterRequest(BaseModel):
    """Request schema for user registration"""
    platform: PlatformType
    language: str = Field(default="ru", max_length=10)
    telegram_id: Optional[int] = None
    username: Optional[str] = Field(None, max_length=255)
    referral_code: Optional[str] = Field(None, max_length=50)


class RegisterResponse(BaseModel):
    """Response schema for user registration"""
    access_code: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    platform: PlatformType

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Request schema for user login"""
    access_code: str = Field(
        ...,
        min_length=11,
        max_length=11,
        pattern=r"^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}$",
        description="Access code in format XXX-XXX-XXX (excludes I, O, 0, 1)",
        json_schema_extra={"example": "ABC-DEF-GH2"}
    )
    
    @field_validator('access_code')
    @classmethod
    def normalize_access_code(cls, v: str) -> str:
        """Convert access code to uppercase for case-insensitive validation"""
        return v.upper()


class LoginResponse(BaseModel):
    """Response schema for user login"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    access_code: str
    platform_registered: PlatformType
    balance: Decimal
    telegram_id: Optional[List[int]] = None
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class TokenVerifyResponse(BaseModel):
    """Response schema for token verification"""
    valid: bool
    user_id: Optional[int] = None
    access_code: Optional[str] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LinkTelegramRequest(BaseModel):
    """Request schema for linking Telegram account"""
    telegram_id: int = Field(..., gt=0, description="Telegram user ID")
    username: Optional[str] = Field(None, max_length=255, description="Telegram username")


class LinkTelegramResponse(BaseModel):
    """Response schema for linking Telegram account"""
    success: bool
    message: str
    telegram_id: List[int]
    access_code: str

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response schema for refreshing access token"""
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class TelegramAuthRequest(BaseModel):
    """Request schema for Telegram-based authentication"""
    telegram_id: int = Field(..., gt=0, description="Telegram user ID")
    username: Optional[str] = Field(None, max_length=255, description="Telegram username")
    language: str = Field(default="ru", max_length=10, description="User language preference")
    referral_code: Optional[str] = Field(None, max_length=50, description="Referral code if provided")


class TelegramAuthResponse(BaseModel):
    """Response schema for Telegram-based authentication"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    access_code: str
    is_new_user: bool
    platform_registered: PlatformType
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Response schema for API errors"""
    detail: str
    error_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)