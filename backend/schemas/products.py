from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ProxyType(str, Enum):
    """Enumeration of supported proxy types."""
    SOCKS5 = "SOCKS5"
    PPTP = "PPTP"


class ProxyItem(BaseModel):
    """Model for a single proxy in the catalog."""
    product_id: int
    ip: str
    port: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    ISP: Optional[str] = None
    ORG: Optional[str] = None
    speed: Optional[str] = None
    price: Decimal
    datestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": 123,
                "ip": "192.168.1.100",
                "port": "1080",
                "login": "user123",
                "password": "pass456",
                "country": "United States",
                "state": "Florida",
                "city": "Miami",
                "zip": "33101",
                "ISP": "Comcast",
                "ORG": "Comcast Cable",
                "speed": "100mbps",
                "price": "2.00",
                "datestamp": "2025-11-12T10:30:00Z"
            }
        }
    )


class ProductsListResponse(BaseModel):
    """Response for GET /products/socks5 and /products/pptp."""
    products: List[ProxyItem]
    total: int
    page: int = 1
    page_size: int = 10
    has_more: bool
    filters: Dict[str, Optional[str]]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "products": [
                    {
                        "product_id": 123,
                        "ip": "192.168.1.100",
                        "port": "1080",
                        "login": "user123",
                        "password": "pass456",
                        "country": "United States",
                        "state": "Florida",
                        "city": "Miami",
                        "zip": "33101",
                        "ISP": "Comcast",
                        "ORG": "Comcast Cable",
                        "speed": "100mbps",
                        "price": "2.00",
                        "datestamp": "2025-11-12T10:30:00Z"
                    }
                ],
                "total": 150,
                "page": 1,
                "page_size": 10,
                "has_more": True,
                "filters": {
                    "country": "United States",
                    "state": "Florida",
                    "city": None,
                    "zip": None
                }
            }
        }
    )


class CountryListItem(BaseModel):
    """Model for available country in the catalog."""
    country: str
    country_code: str
    flag: str
    available_count: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "country": "United States",
                "country_code": "US",
                "flag": "🇺🇸",
                "available_count": 150
            }
        }
    )


class StateListItem(BaseModel):
    """Model for available state/region in the catalog."""
    state: str
    available_count: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "state": "Florida",
                "available_count": 25
            }
        }
    )