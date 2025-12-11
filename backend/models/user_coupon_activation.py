from sqlalchemy import Index, String, Integer, DateTime, Numeric, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class UserCouponActivation(Base):
    __tablename__ = "user_coupon_activation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    coupon_id: Mapped[int] = mapped_column(Integer, ForeignKey('coupons.id_cupon', ondelete='CASCADE'), nullable=False)
    coupon: Mapped[str] = mapped_column(String(50))
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    discount_applied: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))

    user: Mapped["User"] = relationship("User", back_populates="coupon_activations")
    coupon_relation: Mapped["Coupon"] = relationship("Coupon", back_populates="activations")

    __table_args__ = (
        Index('idx_user_coupon_activation_user_id', 'user_id'),
        Index('idx_user_coupon_activation_coupon_id', 'coupon_id'),
        Index('idx_user_coupon_activation_datestamp', 'datestamp'),
        UniqueConstraint('user_id', 'coupon_id', name='uq_user_coupon_once'),
    )