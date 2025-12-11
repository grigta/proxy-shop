"""
External Proxy Schemas

Pydantic schemas for external SOCKS5 proxy API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class ExternalProxyFilterRequest(BaseModel):
    """Request schema for filtering external proxies."""
    country_code: Optional[str] = Field(None, description="Country code (US, UK, etc.)")
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="Region/state name")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    isp: Optional[str] = Field(None, description="ISP name")
    residential: bool = Field(True, description="Include residential proxies")
    mobile: bool = Field(True, description="Include mobile proxies")
    hosting: bool = Field(True, description="Include hosting/datacenter proxies")
    page: int = Field(0, ge=0, description="Page number (0-indexed)")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")


class ExternalProxyResponse(BaseModel):
    """Response schema for a single external proxy."""
    product_id: int = Field(..., description="Internal product ID")
    proxy_id: int = Field(..., description="External API proxy ID")
    country: str = Field(..., description="Country name")
    country_code: str = Field(..., description="Country code")
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="Region/state name")
    zip: Optional[str] = Field(None, description="ZIP code")
    ISP: Optional[str] = Field(None, description="ISP name")
    speed: Optional[str] = Field(None, description="Connection speed (Mbps)")
    mobile: bool = Field(False, description="Is mobile proxy")
    hosting: bool = Field(False, description="Is hosting/datacenter proxy")
    price: float = Field(..., description="Price in USD")
    status: int = Field(..., description="Proxy status (1=online, 0=offline)")

    class Config:
        from_attributes = True


class ExternalProxyListResponse(BaseModel):
    """Response schema for list of external proxies."""
    proxies: List[ExternalProxyResponse]
    total: int = Field(..., description="Total number of proxies available")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")


class ExternalProxyPurchaseRequest(BaseModel):
    """Request schema for purchasing an external proxy."""
    product_id: int = Field(..., description="Internal product ID to purchase", gt=0)

    @field_validator('product_id')
    @classmethod
    def validate_product_id(cls, v):
        if v <= 0:
            raise ValueError("product_id must be a positive integer")
        return v


class ExternalProxyPurchaseResponse(BaseModel):
    """Response schema for successful proxy purchase."""
    order_id: str = Field(..., description="Unique order ID")
    proxy_id: int = Field(..., description="External API proxy ID")
    credentials: dict = Field(..., description="Proxy connection credentials")
    price: Decimal = Field(..., description="Purchase price")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    refundable: bool = Field(..., description="Whether proxy is refundable")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class ExternalProxyRefundRequest(BaseModel):
    """Request schema for refunding a proxy."""
    order_id: str = Field(..., description="Order ID to refund", min_length=1)

    @field_validator('order_id')
    @classmethod
    def validate_order_id(cls, v):
        if not v or not v.strip():
            raise ValueError("order_id cannot be empty")
        return v.strip()


class ExternalProxyRefundResponse(BaseModel):
    """Response schema for successful refund."""
    status: str = Field(..., description="Refund status")
    message: str = Field(..., description="Refund message")
    refund_amount: float = Field(..., description="Amount refunded in USD")


class ExternalProxySyncRequest(BaseModel):
    """Request schema for manual proxy synchronization (admin only)."""
    country_code: Optional[str] = Field(None, description="Filter by country code")
    city: Optional[str] = Field(None, description="Filter by city")
    region: Optional[str] = Field(None, description="Filter by region")
    page_size: int = Field(100, ge=10, le=500, description="Number of proxies to sync")


class ExternalProxySyncResponse(BaseModel):
    """Response schema for synchronization results."""
    total_fetched: int = Field(..., description="Number of proxies fetched from API")
    total_available_external: int = Field(..., description="Total proxies available in external API")
    added: int = Field(..., description="Number of new proxies added")
    updated: int = Field(..., description="Number of proxies updated")
    skipped: int = Field(..., description="Number of proxies skipped")
    sync_time: str = Field(..., description="Timestamp of sync operation")


class ExternalProxyCredentials(BaseModel):
    """Schema for external proxy credentials."""
    ip: str = Field(..., description="Proxy IP address")
    port: str = Field(..., description="Proxy port")
    login: str = Field(..., description="Authentication username")
    password: str = Field(..., description="Authentication password")
    country: Optional[str] = Field(None, description="Country")
    city: Optional[str] = Field(None, description="City")
    region: Optional[str] = Field(None, description="Region")
    zip: Optional[str] = Field(None, description="ZIP code")
    ISP: Optional[str] = Field(None, description="ISP name")
    ORG: Optional[str] = Field(None, description="Organization name")
    speed: Optional[str] = Field(None, description="Connection speed")
    server_ip: Optional[str] = Field(None, description="Server IP address")
    refundable: bool = Field(True, description="Whether proxy is refundable")

    class Config:
        from_attributes = True


class ExternalProxyStatsResponse(BaseModel):
    """Response schema for external proxy statistics."""
    total_inventory: int = Field(..., description="Total external proxies in inventory")
    total_sold: int = Field(..., description="Total external proxies sold")
    total_refunded: int = Field(..., description="Total refunds processed")
    revenue: float = Field(..., description="Total revenue from external proxies")
    countries_available: int = Field(..., description="Number of countries available")
    last_sync: Optional[str] = Field(None, description="Last synchronization timestamp")
