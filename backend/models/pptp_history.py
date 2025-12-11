from sqlalchemy import Index, String, Integer, DateTime, Numeric, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class PptpHistory(Base):
    __tablename__ = "pptp_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('products.product_id', ondelete='SET NULL'), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    wroted_settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pptp: Mapped[str] = mapped_column(Text)
    isRefunded: Mapped[bool] = mapped_column(Boolean, default=False)
    resaled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false', comment='Whether PPTP was resold (1) or invalid (0)')
    user_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment='User key (0 for invalid PPTP)')
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hours_left: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="pptp_purchases")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="pptp_history")

    __table_args__ = (
        Index('idx_pptp_history_user_id', 'user_id'),
        Index('idx_pptp_history_datestamp', 'datestamp'),
        Index('idx_pptp_history_isRefunded', 'isRefunded'),
        Index('idx_pptp_history_expires_at', 'expires_at'),
        Index('idx_pptp_history_resaled', 'resaled'),
        Index('idx_pptp_history_user_key', 'user_key'),
    )