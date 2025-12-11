from sqlalchemy import Index, String, Integer, BigInteger, DateTime, Numeric, ForeignKey, Boolean, Enum, func, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import enum

from backend.core.database import Base


class PlatformType(enum.Enum):
    telegram = "telegram"
    web = "web"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default='ru')
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=Decimal('0.00'))
    user_referal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=True)
    myreferal_id: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)), nullable=True)
    referal_quantity: Mapped[int] = mapped_column(Integer, default=0)
    balance_forward: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=True)

    access_code: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    telegram_id: Mapped[Optional[List[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    platform_registered: Mapped[PlatformType] = mapped_column(Enum(PlatformType, name="platform_type"), nullable=False, server_default='web')
    
    # Admin fields
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    blocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    addresses: Mapped[List["UserAddress"]] = relationship(
        "UserAddress", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["UserTransaction"]] = relationship(
        "UserTransaction", back_populates="user"
    )
    logs: Mapped[List["UserLog"]] = relationship(
        "UserLog", back_populates="user"
    )
    proxy_purchases: Mapped[List["ProxyHistory"]] = relationship(
        "ProxyHistory", back_populates="user"
    )
    pptp_purchases: Mapped[List["PptpHistory"]] = relationship(
        "PptpHistory", back_populates="user"
    )
    coupon_activations: Mapped[List["UserCouponActivation"]] = relationship(
        "UserCouponActivation", back_populates="user"
    )
    pending_invoices: Mapped[List["PendingInvoice"]] = relationship(
        "PendingInvoice", back_populates="user", cascade="all, delete-orphan"
    )
    referrer: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[user_id], backref="referrals", foreign_keys=[user_referal_id]
    )
    balance_owner: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[user_id], foreign_keys=[balance_forward]
    )

    __table_args__ = (
        Index('idx_users_datestamp', 'datestamp'),
        Index('idx_users_is_admin', 'is_admin'),
        Index('idx_users_is_blocked', 'is_blocked'),
        CheckConstraint('balance >= 0', name='check_balance_positive'),
    )