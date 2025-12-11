"""
Proxy Inventory model for admin panel to manage available proxies.
Stores IP, port, location, availability, and pricing information.
"""

from sqlalchemy import Index, String, Integer, DateTime, Numeric, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class ProxyInventory(Base):
    """
    Model for storing proxy inventory.
    Used by admins to manage catalog of available proxies.
    
    Each proxy has unique IP:port combination, location data (country/state/city),
    availability flag, and price per hour.
    """
    __tablename__ = "proxy_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True, comment="IP address (IPv4 or IPv6)")
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="Port number (1-65535)")
    country: Mapped[str] = mapped_column(String(100), nullable=False, comment="Country")
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="State/Region")
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="City")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Is proxy available for purchase")
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=Decimal('0.01'), nullable=False, comment="Price per hour in USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="Creation date")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Last update date")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="Additional notes for admins")

    __table_args__ = (
        Index('idx_proxy_inventory_ip_port', 'ip', 'port', unique=True),  # Unique IP:port combination
        Index('idx_proxy_inventory_available', 'is_available'),  # Fast search for available proxies
        Index('idx_proxy_inventory_location', 'country', 'state', 'city'),  # Search by location
        {"comment": "Proxy inventory for admin management"}
    )

