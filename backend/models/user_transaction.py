from sqlalchemy import Index, String, Integer, DateTime, Numeric, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class UserTransaction(Base):
    """
    User transaction model supporting both legacy cryptocurrency transactions 
    and new Heleket payment invoices.
    
    Legacy transactions have: chain, currency, from_address, to_address, txid
    Heleket transactions have: payment_uuid, payment_url, order_id
    
    The transaction_type field distinguishes between 'legacy' and 'heleket' transactions.
    """
    __tablename__ = "user_transactions"

    id_tranz: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    chain: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(20))
    from_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    txid: Mapped[str] = mapped_column(String(255), unique=True)
    fee: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    amount_in_dollar: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    dateOfTransaction: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transId: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    coin_amount: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    coin_course: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    
    # Heleket payment fields
    payment_uuid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment='Heleket payment UUID')
    payment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment='Heleket payment URL')
    order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment='Merchant order identifier')
    
    # Transaction type: 'legacy' for cryptocurrencyapi.net, 'heleket' for Heleket payments
    transaction_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default='legacy', comment='Transaction source: legacy or heleket')

    user: Mapped["User"] = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index('idx_user_transactions_user_id', 'user_id'),
        Index('idx_user_transactions_date', 'dateOfTransaction'),
        Index('idx_user_transactions_payment_uuid', 'payment_uuid'),
    )