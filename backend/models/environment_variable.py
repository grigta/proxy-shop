from sqlalchemy import Index, String, Integer, DateTime, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime

from backend.core.database import Base


class EnvironmentVariable(Base):
    """
    Environment variables storage for dynamic configuration.

    This table allows changing application configuration without restarting the application.
    All services should fetch values from DB using helper methods.

    Examples of variables for User Profile & Referral API:
    - BOT_USERNAME = 'proxy_shop_bot' - Telegram bot username for referral links
    - WEB_REFERRAL_BASE_URL = 'https://proxy-shop.com/register' - Base URL for web referral links
    - REFERRAL_BONUS_PERCENTAGE = '10' - Percentage bonus for referrers
    - REFERRAL_BONUS_ON_FIRST_PURCHASE = 'true' - Award bonus only on first purchase

    Examples of variables for other modules:
    - SUPPORT_TELEGRAM_ID = '8171638354' - Support Telegram ID
    - RULES_TELEGRAPH_URL = 'https://telegra.ph/proxy-shop-rules' - Link to rules
    - SOCKS5_PRICE_USD = '2.0' - SOCKS5 proxy price
    - PPTP_PRICE_USD = '5.0' - PPTP proxy price
    - SOCKS5_REFUND_MINUTES = '30' - Refund window for SOCKS5
    - PPTP_REFUND_HOURS = '24' - Refund window for PPTP
    """
    __tablename__ = "environment_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    data: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    data_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
    )