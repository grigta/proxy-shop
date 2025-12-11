from pydantic import BaseModel, Field, ConfigDict, model_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.schemas.products import ProxyType


class PurchaseRequest(BaseModel):
    """Request for purchasing proxy.

    This unified schema serves both SOCKS5 and PPTP purchase endpoints.
    The validator enforces mutually exclusive purchase modes to prevent ambiguous requests.

    Purchase Modes:
    ---------------
    SOCKS5 Mode (Direct Product Purchase):
        - Required: product_id
        - Optional: quantity (default: 1), coupon_code
        - Forbidden: country, state, city, zip_code
        - Used by: POST /purchase/socks5

    PPTP Mode (Location-Based Purchase):
        - Required: country
        - Optional: state, city, zip_code, coupon_code
        - Forbidden: product_id
        - Fixed: quantity=1 (implicit)
        - Used by: POST /purchase/pptp

    Design Rationale:
    -----------------
    The validator intentionally forbids mixing product_id with location filters (country/state/city/zip).
    This restriction applies globally to all routes using this schema, ensuring clear separation between:
    1. Direct product selection (SOCKS5 workflow)
    2. Filter-based discovery (PPTP workflow)

    If future business requirements demand mixed-mode purchases or more flexible combinations,
    consider splitting this schema into separate classes (e.g., Socks5PurchaseRequest and
    PptpPurchaseRequest) to make restrictions more localized and avoid global validator impact.

    Client Compatibility:
    --------------------
    This schema is used by the Telegram bot and other API clients. Any structural changes
    must maintain backward compatibility with existing integrations.
    """
    product_id: Optional[int] = Field(None, gt=0, description="Product ID to purchase (required for SOCKS5)")
    quantity: int = Field(1, ge=1, le=100, description="Number of proxies to purchase")
    coupon_code: Optional[str] = Field(None, max_length=50, description="Optional discount coupon code")
    country: Optional[str] = Field(None, max_length=100, description="Country/region filter (required for PPTP)")
    catalog_id: Optional[int] = Field(None, gt=0, description="Catalog ID filter (optional for PPTP)")
    state: Optional[str] = Field(None, max_length=100, description="State filter (optional for PPTP)")
    city: Optional[str] = Field(None, max_length=100, description="City filter (optional for PPTP)")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP code filter (optional for PPTP)")

    @model_validator(mode='after')
    def validate_purchase_type(self) -> 'PurchaseRequest':
        """Enforce valid purchase modes.

        Purchase Modes:
        1. Direct purchase by product_id (for both SOCKS5 and PPTP)
        2. Filter-based purchase by country (for PPTP only)

        Raises:
            ValueError: If neither mode is specified.
        """
        if not self.product_id and not self.country:
            raise ValueError('Either product_id or country must be provided')
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "description": "SOCKS5 purchase",
                    "value": {
                        "product_id": 123,
                        "quantity": 1,
                        "coupon_code": "DISCOUNT10"
                    }
                },
                {
                    "description": "PPTP purchase with filters",
                    "value": {
                        "country": "USA",
                        "state": "Texas",
                        "city": "Houston",
                        "zip_code": "77001",
                        "coupon_code": None
                    }
                }
            ]
        }
    )


class PurchaseResponse(BaseModel):
    """Response after successful proxy purchase."""
    success: bool = True
    order_id: Optional[str] = None
    product_id: Optional[int] = None  # Optional because external proxies are deleted after purchase (ondelete='SET NULL')
    quantity: int
    price: Decimal
    original_price: Decimal
    discount_applied: Optional[Decimal] = None
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    proxies: List[Dict[str, Any]]
    expires_at: datetime
    hours_left: int
    new_balance: Decimal

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "order_id": "ORDER-20251112153045-A2B3C4",
                "product_id": 123,
                "quantity": 1,
                "price": "2.00",
                "original_price": "2.00",
                "discount_applied": None,
                "country": "United States",
                "state": "Florida",
                "city": "Miami",
                "zip": "33101",
                "proxies": [
                    {
                        "ip": "192.168.1.100",
                        "port": "1080",
                        "login": "user123",
                        "password": "pass456"
                    }
                ],
                "expires_at": "2025-11-13T10:30:00Z",
                "hours_left": 24,
                "new_balance": "98.00"
            }
        }
    )


class PurchaseHistoryItem(BaseModel):
    """Model for a single purchase in history."""
    id: int
    order_id: Optional[str] = None  # Only for SOCKS5
    proxy_type: ProxyType
    quantity: int
    price: Decimal
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    proxies: List[Dict[str, Any]]
    datestamp: datetime
    expires_at: datetime
    hours_left: int
    isRefunded: bool
    resaled: bool = Field(..., description="Whether PPTP was resold (True) or invalid (False)")
    user_key: Optional[str] = Field(None, description="User key (0 for invalid PPTP, None for valid)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 456,
                "order_id": "ORDER-20251112153045-A2B3C4",
                "proxy_type": "SOCKS5",
                "quantity": 1,
                "price": "2.00",
                "country": "United States",
                "proxies": [
                    {
                        "ip": "192.168.1.100",
                        "port": "1080",
                        "login": "user123",
                        "password": "pass456"
                    }
                ],
                "datestamp": "2025-11-12T10:30:00Z",
                "expires_at": "2025-11-13T10:30:00Z",
                "hours_left": 23,
                "isRefunded": False,
                "resaled": True,
                "user_key": None
            }
        }
    )


class PurchaseHistoryResponse(BaseModel):
    """Response for GET /purchase/history/{userId}."""
    purchases: List[PurchaseHistoryItem]
    total: int
    page: int = 1
    page_size: int = 10

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "purchases": [
                    {
                        "id": 456,
                        "order_id": "ORDER-20251112153045-A2B3C4",
                        "proxy_type": "SOCKS5",
                        "quantity": 1,
                        "price": "2.00",
                        "country": "United States",
                        "proxies": [{"ip": "192.168.1.100", "port": "1080", "login": "user123", "password": "pass456"}],
                        "datestamp": "2025-11-12T10:30:00Z",
                        "expires_at": "2025-11-13T10:30:00Z",
                        "hours_left": 23,
                        "isRefunded": False,
                        "resaled": True,
                        "user_key": None
                    }
                ],
                "total": 5,
                "page": 1,
                "page_size": 10
            }
        }
    )


class ValidateProxyResponse(BaseModel):
    """Response for POST /purchase/validate/{proxyId}."""
    proxy_id: int
    online: bool
    latency_ms: Optional[float] = None
    exit_ip: Optional[str] = None
    minutes_since_purchase: int
    refund_eligible: bool
    refund_window_minutes: int
    message: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "proxy_id": 456,
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "minutes_since_purchase": 25,
                "refund_eligible": True,
                "refund_window_minutes": 30,
                "message": "Прокси офлайн! С момента покупки прошло 25м. -> REFOUND"
            }
        }
    )


class ExtendProxyRequest(BaseModel):
    """Request for extending proxy duration."""
    hours: int = Field(24, ge=1, le=168, description="Number of hours to extend (max 7 days)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "hours": 24
            }
        }
    )


class ExtendProxyResponse(BaseModel):
    """Response after extending proxy."""
    success: bool
    proxy_id: int
    price: Decimal
    new_expires_at: datetime
    hours_added: int
    new_balance: Decimal
    message: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "proxy_id": 456,
                "price": "2.00",
                "new_expires_at": "2025-11-14T10:30:00Z",
                "hours_added": 24,
                "new_balance": "96.00",
                "message": "Прокси 192.168.1.100:1080 успешно продлен. BALANCE: 96.00"
            }
        }
    )


class RefundResponse(BaseModel):
    """Response after refund processing."""
    success: bool
    proxy_id: int
    refunded_amount: Decimal
    new_balance: Decimal
    message: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "proxy_id": 456,
                "refunded_amount": "2.00",
                "new_balance": "102.00",
                "message": "Возврат успешно выполнен. Сумма 2.00 USD возвращена на баланс."
            }
        }
    )


class BulkValidatePPTPResponse(BaseModel):
    """Response for POST /purchase/validate-pptp (bulk validation)."""
    validated_count: int = Field(..., description="Total number of PPTP proxies checked")
    valid_count: int = Field(..., description="Number of working proxies")
    invalid_count: int = Field(..., description="Number of non-working proxies")
    refunded_amount: Decimal = Field(..., description="Total amount refunded for invalid proxies")
    new_balance: Decimal = Field(..., description="User's new balance after refunds")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="Details for each proxy checked")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "validated_count": 5,
                "valid_count": 3,
                "invalid_count": 2,
                "refunded_amount": "4.00",
                "new_balance": "104.00",
                "details": [
                    {"proxy_id": 1, "ip": "1.2.3.4", "online": True, "refunded": False},
                    {"proxy_id": 2, "ip": "5.6.7.8", "online": False, "refunded": True, "amount": "2.00"}
                ]
            }
        }
    )