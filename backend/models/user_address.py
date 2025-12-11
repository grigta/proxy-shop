from sqlalchemy import Index, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

from backend.core.database import Base


class UserAddress(Base):
    """
    DEPRECATED: Legacy model for storing per-chain cryptocurrency addresses.
    
    This model was used with the old cryptocurrencyapi.net integration where each user
    had dedicated addresses for BTC, ETH, LTC, BNB, and USDT variants.
    
    With the Heleket migration (Mode B), users no longer have dedicated addresses.
    Instead, they receive universal payment links where they select the cryptocurrency
    on Heleket's hosted page.
    
    This model is retained for:
    1. Historical data access - existing addresses in the database
    2. Transaction history display - showing which addresses were used
    3. Backward compatibility - legacy API endpoints that return address info
    
    New payment flows do NOT create or update records in this table.
    
    Future: This model may be removed once all legacy transaction references are migrated
    or after a sufficient retention period for historical data.
    """
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    usdt_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    btc_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ltc_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    eth_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bnb_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    usdt_date_of_gen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    btc_date_of_gen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ltc_date_of_gen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    eth_date_of_gen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    bnb_date_of_gen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="addresses")

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_addresses_user_id'),
    )