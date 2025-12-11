from sqlalchemy import Index, String, Integer, DateTime, Numeric, ForeignKey, Boolean, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class ProxyHistory(Base):
    __tablename__ = "proxy_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('products.product_id', ondelete='SET NULL'), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    order_id: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    country: Mapped[str] = mapped_column(String(100))
    proxies: Mapped[str] = mapped_column(Text)
    isRefunded: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hours_left: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="proxy_purchases")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="proxy_history")

    __table_args__ = (
        Index('idx_proxy_history_user_id', 'user_id'),
        Index('idx_proxy_history_order_id', 'order_id'),
        Index('idx_proxy_history_datestamp', 'datestamp'),
        Index('idx_proxy_history_isRefunded', 'isRefunded'),
        Index('idx_proxy_history_expires_at', 'expires_at'),
        UniqueConstraint('order_id', name='uq_proxy_history_order_id'),
    )