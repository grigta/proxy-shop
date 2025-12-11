"""
Pending invoice model for tracking payment invoices before completion.

This model stores the original invoice amount to ensure correct crediting
when webhooks are received, as Heleket may send crypto amounts instead of USD.
"""
from sqlalchemy import Index, String, Integer, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class PendingInvoice(Base):
    """
    Pending invoice model for tracking Heleket payment invoices.

    Stores the original USD amount requested when creating an invoice,
    so we can use it when the webhook arrives (instead of trusting merchant_amount
    which may contain the crypto amount rather than USD).
    """
    __tablename__ = "pending_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    payment_uuid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment='Heleket payment UUID')
    order_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment='Merchant order identifier')
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False, comment='Original invoice amount in USD')
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='pending/completed/expired')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    webhook_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=20, scale=8), nullable=True, comment='Amount from webhook for comparison')

    user: Mapped["User"] = relationship("User", back_populates="pending_invoices")

    __table_args__ = (
        Index('idx_pending_invoices_user_id', 'user_id'),
        Index('idx_pending_invoices_status', 'status'),
        Index('idx_pending_invoices_created_at', 'created_at'),
    )
