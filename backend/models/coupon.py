from sqlalchemy import Index, String, Integer, DateTime, Numeric, Boolean, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id_cupon: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    coupon: Mapped[str] = mapped_column(String(50), unique=True)
    usage_quantity: Mapped[int] = mapped_column(Integer, default=0)
    max_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    activations: Mapped[List["UserCouponActivation"]] = relationship("UserCouponActivation", back_populates="coupon_relation")

    __table_args__ = (
        Index('idx_coupons_is_active', 'is_active'),
        CheckConstraint('discount_percentage >= 0 AND discount_percentage <= 100', name='check_discount_range'),
        CheckConstraint('usage_quantity >= 0', name='check_usage_positive'),
    )