"""
Pydantic schemas for request/response validation.
"""

# Authentication schemas
from backend.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenVerifyResponse,
    LinkTelegramRequest,
    LinkTelegramResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)

# Payment schemas
from backend.schemas.payment import (
    # Active Heleket schemas
    CreatePaymentRequest,
    CreatePaymentResponse,
    HeleketWebhookPayload,
    TransactionHistoryItem,
    TransactionHistoryResponse,
    IPNWebhookResponse,
    DepositSuccessNotification,
    # Legacy schemas for backward compatibility
    CryptoChain,
    GenerateAddressRequest,
    GenerateAddressResponse,
    IPNWebhookPayload
)

# Products schemas
from backend.schemas.products import (
    ProxyType,
    ProxyItem,
    ProductsListResponse,
    CountryListItem,
    StateListItem
)

# Purchase schemas
from backend.schemas.purchase import (
    PurchaseRequest,
    PurchaseResponse,
    PurchaseHistoryItem,
    PurchaseHistoryResponse,
    ValidateProxyResponse,
    ExtendProxyRequest,
    ExtendProxyResponse,
    RefundResponse
)

# User schemas
from backend.schemas.user import (
    UserProfileResponse,
    UserHistoryItem,
    UserHistoryResponse,
    ReferralItem,
    ReferralsResponse,
    ActivateCouponRequest,
    ActivateCouponResponse
)

# Admin schemas
from backend.schemas.admin import (
    PeriodStats,
    DashboardStatsResponse,
    RevenueChartData,
    AdminUserListItem,
    AdminUserListResponse,
    UpdateUserRequest,
    UserFilters,
    AdminCouponListItem,
    CreateCouponRequest,
    UpdateCouponRequest,
    AdminCouponListResponse,
    CouponFilters,
    ProxyInventoryItem,
    CreateProxyRequest,
    BulkCreateProxiesRequest,
    UpdateProxyAvailabilityRequest,
    ProxyInventoryFilters,
    AdminProxyListResponse
)

__all__ = [
    # Auth schemas
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenVerifyResponse",
    "LinkTelegramRequest",
    "LinkTelegramResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    # Payment schemas
    "CreatePaymentRequest",
    "CreatePaymentResponse",
    "HeleketWebhookPayload",
    "TransactionHistoryItem",
    "TransactionHistoryResponse",
    "IPNWebhookResponse",
    "DepositSuccessNotification",
    # Legacy payment schemas (for backward compatibility)
    "CryptoChain",
    "GenerateAddressRequest",
    "GenerateAddressResponse",
    "IPNWebhookPayload",
    # Products schemas
    "ProxyType",
    "ProxyItem",
    "ProductsListResponse",
    "CountryListItem",
    "StateListItem",
    # Purchase schemas
    "PurchaseRequest",
    "PurchaseResponse",
    "PurchaseHistoryItem",
    "PurchaseHistoryResponse",
    "ValidateProxyResponse",
    "ExtendProxyRequest",
    "ExtendProxyResponse",
    "RefundResponse",
    # User schemas
    "UserProfileResponse",
    "UserHistoryItem",
    "UserHistoryResponse",
    "ReferralItem",
    "ReferralsResponse",
    "ActivateCouponRequest",
    "ActivateCouponResponse",
    # Admin schemas
    "PeriodStats",
    "DashboardStatsResponse",
    "RevenueChartData",
    "AdminUserListItem",
    "AdminUserListResponse",
    "UpdateUserRequest",
    "UserFilters",
    "AdminCouponListItem",
    "CreateCouponRequest",
    "UpdateCouponRequest",
    "AdminCouponListResponse",
    "CouponFilters",
    "ProxyInventoryItem",
    "CreateProxyRequest",
    "BulkCreateProxiesRequest",
    "UpdateProxyAvailabilityRequest",
    "ProxyInventoryFilters",
    "AdminProxyListResponse"
]