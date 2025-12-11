"""
Admin API schemas for dashboard statistics, user management, coupons, and proxy inventory.
All schemas are designed for Russian-language admin panel.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.models.user import PlatformType


class PeriodStats(BaseModel):
    """
    Statistics for a specific time period.
    Used in dashboard to show revenue, purchases, deposits for 1d/7d/30d/all_time.
    """
    revenue: Decimal = Field(..., description="Total revenue (SUM from proxy_history + pptp_history)")
    proxy_revenue: Decimal = Field(default=Decimal('0'), description="Revenue from proxy sales")
    pptp_revenue: Decimal = Field(default=Decimal('0'), description="Revenue from PPTP sales")
    purchases: int = Field(..., description="Number of purchases")
    deposits: Decimal = Field(..., description="Sum of deposits (SUM from user_transactions)")
    deposits_count: int = Field(..., description="Number of deposit transactions")
    new_users: int = Field(..., description="New users registered in period")
    refunds: int = Field(..., description="Number of refunds")
    refunds_amount: Decimal = Field(..., description="Total refund amount")
    net_profit: Decimal = Field(default=Decimal('0'), description="Net profit (revenue - refunds)")

    # Percentage changes compared to previous period
    deposits_change_percent: float = Field(default=0.0, description="Deposits change percentage")
    users_change_percent: float = Field(default=0.0, description="Users change percentage")
    proxy_revenue_change_percent: float = Field(default=0.0, description="Proxy revenue change percentage")
    pptp_revenue_change_percent: float = Field(default=0.0, description="PPTP revenue change percentage")
    refunds_change_percent: float = Field(default=0.0, description="Refunds change percentage")
    net_profit_change_percent: float = Field(default=0.0, description="Net profit change percentage")

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    """
    Response schema for GET /api/admin/stats endpoint.
    Comprehensive dashboard statistics with period-based aggregations.
    
    Example:
        {
            "total_users": 1500,
            "total_revenue": "125000.50",
            "total_purchases": 3500,
            "total_deposits": "150000.00",
            "active_proxies": 450,
            "refunded_count": 50,
            "period_stats": {
                "1d": {...},
                "7d": {...},
                "30d": {...},
                "all_time": {...}
            }
        }
    """
    total_users: int = Field(..., description="Total users in system")
    total_revenue: Decimal = Field(..., description="Total revenue (all time)")
    total_purchases: int = Field(..., description="Total purchases (all time)")
    total_deposits: Decimal = Field(..., description="Total deposits (all time)")
    active_proxies: int = Field(..., description="Active proxies (not expired, not refunded)")
    refunded_count: int = Field(..., description="Total refunds count")
    period_stats: Dict[str, PeriodStats] = Field(..., description="Statistics by periods (1d, 7d, 30d, all_time)")

    model_config = ConfigDict(from_attributes=True)


class RevenueChartData(BaseModel):
    """
    Data point for revenue charts (LineChart, BarChart).
    Used in GET /api/admin/revenue-chart endpoint.
    
    Example:
        {
            "date": "2025-11-12",
            "revenue": "5000.50",
            "purchases": 50,
            "deposits": "6000.00",
            "socks5_count": 30,
            "pptp_count": 20
        }
    """
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    revenue: Decimal = Field(..., description="Revenue for this period")
    purchases: int = Field(..., description="Number of purchases")
    deposits: Decimal = Field(..., description="Sum of deposits")
    socks5_count: int = Field(..., description="Number of SOCKS5 purchases")
    pptp_count: int = Field(..., description="Number of PPTP purchases")

    model_config = ConfigDict(from_attributes=True)


class AdminUserListItem(BaseModel):
    """
    User item in admin users list with aggregated statistics.
    Used in GET /api/admin/users endpoint.
    """
    user_id: int = Field(..., description="User ID")
    access_code: str = Field(..., description="Access code")
    balance: Decimal = Field(..., description="Current balance")
    datestamp: datetime = Field(..., description="Registration date")
    platform_registered: PlatformType = Field(..., description="Registration platform")
    language: str = Field(..., description="Interface language")
    username: Optional[str] = Field(None, description="Username")
    telegram_id: Optional[int] = Field(None, description="Telegram ID of the account owner (first element)")
    telegram_id_list: Optional[List[int]] = Field(None, description="Full list of linked Telegram IDs")

    # Aggregated statistics
    total_spent: Decimal = Field(..., description="Total spent (SUM of purchases)")
    total_deposited: Decimal = Field(..., description="Total deposited (SUM of transactions)")
    purchases_count: int = Field(..., description="Number of purchases")
    last_activity: Optional[datetime] = Field(None, description="Last activity date")
    is_blocked: bool = Field(False, description="Is user blocked")
    blocked_at: Optional[datetime] = Field(None, description="Block date")
    referrals_count: int = Field(0, description="Number of referrals")

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """
    Response schema for GET /api/admin/users endpoint.
    Paginated users list with filters.
    """
    users: List[AdminUserListItem] = Field(..., description="List of users")
    total: int = Field(..., description="Total users count (with filters applied)")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRequest(BaseModel):
    """
    Request schema for PATCH /api/admin/users/{userId} endpoint.
    Update user data (admin only).
    """
    balance: Optional[Decimal] = Field(None, ge=0, description="New balance")
    is_blocked: Optional[bool] = Field(None, description="Block/unblock user")
    blocked_reason: Optional[str] = Field(None, max_length=500, description="Block reason")
    language: Optional[str] = Field(None, max_length=10, description="Interface language")

    @field_validator('blocked_reason')
    @classmethod
    def validate_blocked_reason(cls, v, info):
        """Validate that blocked_reason is required when blocking user"""
        if info.data.get('is_blocked') is True and not v:
            raise ValueError('blocked_reason is required when blocking user')
        return v

    model_config = ConfigDict(from_attributes=True)


class UserFilters(BaseModel):
    """
    Filters for GET /api/admin/users endpoint.
    All filters are optional.
    """
    search: Optional[str] = Field(None, description="Search by username, access_code, telegram_id")
    platform: Optional[PlatformType] = Field(None, description="Filter by platform")
    date_from: Optional[datetime] = Field(None, description="Registration date from")
    date_to: Optional[datetime] = Field(None, description="Registration date to")
    min_balance: Optional[Decimal] = Field(None, ge=0, description="Minimum balance")
    max_balance: Optional[Decimal] = Field(None, ge=0, description="Maximum balance")
    is_blocked: Optional[bool] = Field(None, description="Filter by blocked status")

    model_config = ConfigDict(from_attributes=True)


# Coupon schemas

class AdminCouponListItem(BaseModel):
    """
    Coupon item in admin coupons list.
    Used in GET /api/admin/coupons endpoint.
    """
    id: int = Field(..., description="Coupon ID")
    code: str = Field(..., description="Coupon code")
    discount_percent: Decimal = Field(..., description="Discount percentage (0-100)")
    max_uses: int = Field(..., description="Maximum uses")
    used_count: int = Field(0, description="Current usage count")
    is_active: bool = Field(True, description="Is coupon active")
    created_at: datetime = Field(..., description="Creation date")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")

    model_config = ConfigDict(from_attributes=True)


class CreateCouponRequest(BaseModel):
    """
    Request schema for POST /api/admin/coupons endpoint.
    Create new discount coupon.
    """
    code: str = Field(..., min_length=1, max_length=50, description="Unique coupon code")
    discount_percent: Decimal = Field(..., ge=0, le=100, description="Discount percentage (0-100)")
    max_uses: int = Field(..., ge=1, description="Maximum uses")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    is_active: bool = Field(True, description="Is coupon active")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "code": "SAVE20",
                "discount_percent": "20.00",
                "max_uses": 100,
                "expires_at": "2025-12-31T23:59:59",
                "is_active": True
            }
        }
    )


class UpdateCouponRequest(BaseModel):
    """
    Request schema for PATCH /api/admin/coupons/{couponId} endpoint.
    Update existing coupon.
    """
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum uses")
    is_active: Optional[bool] = Field(None, description="Is coupon active")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")

    model_config = ConfigDict(from_attributes=True)


class AdminCouponListResponse(BaseModel):
    """
    Response schema for GET /api/admin/coupons endpoint.
    Paginated coupons list.
    """
    coupons: List[AdminCouponListItem] = Field(..., description="List of coupons")
    total: int = Field(..., description="Total coupons count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")

    model_config = ConfigDict(from_attributes=True)


class CouponFilters(BaseModel):
    """
    Filters for GET /api/admin/coupons endpoint.
    """
    search: Optional[str] = Field(None, description="Search by code")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    date_from: Optional[datetime] = Field(None, description="Created date from")
    date_to: Optional[datetime] = Field(None, description="Created date to")

    model_config = ConfigDict(from_attributes=True)


# Proxy inventory schemas

class ProxyInventoryItem(BaseModel):
    """
    Proxy item in admin proxy inventory list.
    Used in GET /api/admin/proxies endpoint.
    """
    id: int = Field(..., description="Proxy ID")
    ip: str = Field(..., description="IP address (IPv4 or IPv6)")
    port: int = Field(..., description="Port (1-65535)")
    country: str = Field(..., description="Country")
    state: Optional[str] = Field(None, description="State/Region")
    city: Optional[str] = Field(None, description="City")
    is_available: bool = Field(True, description="Is proxy available")
    price_per_hour: Decimal = Field(..., description="Price per hour in USD")
    created_at: datetime = Field(..., description="Creation date")
    notes: Optional[str] = Field(None, description="Additional notes")

    model_config = ConfigDict(from_attributes=True)


class CreateProxyRequest(BaseModel):
    """
    Request schema for POST /api/admin/proxies endpoint.
    Create single proxy.
    """
    ip: str = Field(..., description="IP address")
    port: int = Field(..., ge=1, le=65535, description="Port")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    state: Optional[str] = Field(None, max_length=100, description="State/Region")
    city: Optional[str] = Field(None, max_length=100, description="City")
    price_per_hour: Decimal = Field(..., gt=0, description="Price per hour in USD")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "ip": "192.168.1.1",
                "port": 1080,
                "country": "United States",
                "state": "California",
                "city": "Los Angeles",
                "price_per_hour": "0.05",
                "notes": "High-speed proxy"
            }
        }
    )


class BulkCreateProxiesRequest(BaseModel):
    """
    Request schema for POST /api/admin/proxies/bulk endpoint.
    Create multiple proxies at once.
    """
    proxies: List[CreateProxyRequest] = Field(..., min_length=1, description="List of proxies to create")

    model_config = ConfigDict(from_attributes=True)


class UpdateProxyAvailabilityRequest(BaseModel):
    """
    Request schema for PATCH /api/admin/proxies/{proxyId} endpoint.
    Update proxy availability and price.
    """
    is_available: bool = Field(..., description="Is proxy available")
    price_per_hour: Optional[Decimal] = Field(None, gt=0, description="Price per hour in USD")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    model_config = ConfigDict(from_attributes=True)


class ProxyInventoryFilters(BaseModel):
    """
    Filters for GET /api/admin/proxies endpoint.
    """
    country: Optional[str] = Field(None, description="Filter by country")
    state: Optional[str] = Field(None, description="Filter by state")
    city: Optional[str] = Field(None, description="Filter by city")
    is_available: Optional[bool] = Field(None, description="Filter by availability")
    search: Optional[str] = Field(None, description="Search by IP or city")

    model_config = ConfigDict(from_attributes=True)


class AdminProxyListResponse(BaseModel):
    """
    Response schema for GET /api/admin/proxies endpoint.
    Paginated proxies list.
    """
    proxies: List[ProxyInventoryItem] = Field(..., description="List of proxies")
    total: int = Field(..., description="Total proxies count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")

    model_config = ConfigDict(from_attributes=True)


# PPTP bulk upload schemas

class BulkCreatePptpRequest(BaseModel):
    """
    Request schema for POST /api/admin/pptp/bulk endpoint.
    Bulk create PPTP proxies from line or CSV format.

    Line format example (colon-separated, one entry per line):
        104.11.157.41:user1:pass123:United States:TX:Houston:77001
        100.12.0.17:admin:secret:United States:NY:NewYork:10001

    CSV format example:
        ip,login,password,country,state,city,zip
        104.11.157.41,user1,pass123,United States,TX,Houston,77001
        100.12.0.17,admin,secret,United States,NY,NewYork,10001
    """
    data: str = Field(..., min_length=1, description="Proxy data in line or CSV format")
    format: Optional[str] = Field(None, description="Format: 'line' or 'csv'. Auto-detect if None")
    catalog_id: Optional[int] = Field(None, description="Existing catalog ID to add proxies to")
    catalog_name: Optional[str] = Field(None, description="Name for new catalog (if creating)")
    catalog_price: Optional[Decimal] = Field(None, description="Price for new catalog (if creating)")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate format value"""
        if v is not None and v not in ['line', 'csv']:
            raise ValueError("format must be 'line' or 'csv'")
        return v

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "data": "104.11.157.41:user1:pass123:United States:TX:Houston:77001\n100.12.0.17:admin:secret:United States:NY:NewYork:10001",
                "format": "line",
                "catalog_name": "USA Premium",
                "catalog_price": "7.50"
            }
        }
    )


class PptpProductItem(BaseModel):
    """
    PPTP product item in response.
    Used in bulk upload response to show created products.
    """
    product_id: int = Field(..., description="Product ID")
    ip: str = Field(..., description="IP address")
    login: str = Field(..., description="Login")
    password: str = Field(..., description="Password")
    country: str = Field(..., description="Country")
    state: str = Field(..., description="State")
    city: str = Field(..., description="City")
    zip: str = Field(..., description="ZIP code")
    created_at: datetime = Field(..., description="Creation date")

    model_config = ConfigDict(from_attributes=True)


class BulkCreatePptpResponse(BaseModel):
    """
    Response schema for POST /api/admin/pptp/bulk endpoint.
    Returns statistics about bulk upload operation.
    """
    success: bool = Field(..., description="Overall operation status")
    message: str = Field(..., description="Result message")
    created_count: int = Field(..., description="Number of successfully created products")
    failed_count: int = Field(..., description="Number of failed entries")
    products: List[PptpProductItem] = Field(..., description="List of created products")
    errors: List[str] = Field(..., description="List of error messages")

    model_config = ConfigDict(from_attributes=True)


class PptpProxyListResponse(BaseModel):
    """
    Response schema for GET /api/admin/pptp endpoint.
    Returns paginated list of PPTP proxies.
    """
    proxies: List[PptpProductItem] = Field(..., description="List of PPTP proxies")
    total: int = Field(..., description="Total number of PPTP proxies")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

    model_config = ConfigDict(from_attributes=True)


class BulkDeletePptpRequest(BaseModel):
    """
    Request schema for DELETE /api/admin/pptp/bulk endpoint.
    Accepts list of product IDs to delete.
    """
    product_ids: List[int] = Field(..., description="List of product IDs to delete", min_length=1)

    model_config = ConfigDict(from_attributes=True)


class BulkDeletePptpResponse(BaseModel):
    """
    Response schema for DELETE /api/admin/pptp/bulk endpoint.
    Returns statistics about bulk delete operation.
    """
    success: bool = Field(..., description="Overall operation status")
    message: str = Field(..., description="Result message")
    deleted_count: int = Field(..., description="Number of successfully deleted products")
    failed_count: int = Field(..., description="Number of failed deletions")
    errors: List[str] = Field(default_factory=list, description="List of error messages")

    model_config = ConfigDict(from_attributes=True)


class CatalogItem(BaseModel):
    """
    Catalog item for dropdown selection.
    """
    id: int = Field(..., description="Catalog ID")
    name: str = Field(..., description="Catalog name (line_name)")
    price: Decimal = Field(..., description="Price in USD")
    ig_catalog: str = Field(..., description="Unique catalog identifier")
    proxy_type: str = Field(..., description="Proxy type (PPTP or SOCKS5)")

    model_config = ConfigDict(from_attributes=True)


class CatalogListResponse(BaseModel):
    """
    Response schema for GET /api/admin/catalogs endpoint.
    Returns list of catalogs for dropdown selection.
    """
    catalogs: List[CatalogItem] = Field(..., description="List of catalogs")
    total: int = Field(..., description="Total number of catalogs")

    model_config = ConfigDict(from_attributes=True)


class UpdateCatalogRequest(BaseModel):
    """
    Request schema for PATCH /api/admin/catalogs/{catalog_id}.
    Updates catalog name, price, or description.
    """
    line_name: Optional[str] = Field(None, description="Catalog display name")
    price: Optional[Decimal] = Field(None, ge=0, description="Price in USD")
    description_ru: Optional[str] = Field(None, description="Russian description")
    description_eng: Optional[str] = Field(None, description="English description")

    model_config = ConfigDict(from_attributes=True)

