"""
Telegram Notification Service for sending messages to users.
Used to notify users about payments, purchases, and other events.
"""

import httpx
import logging
from typing import Optional
from decimal import Decimal
from backend.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending Telegram notifications to users."""

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    @staticmethod
    async def send_telegram_message(
        user_id: int,
        text: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Send a Telegram message to user.

        Args:
            user_id: Telegram user ID (chat_id)
            text: Message text
            parse_mode: Message parse mode (HTML or Markdown)

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            url = NotificationService.TELEGRAM_API_URL.format(
                token=settings.TELEGRAM_BOT_TOKEN
            )

            payload = {
                "chat_id": user_id,
                "text": text,
                "parse_mode": parse_mode
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    logger.info(f"Notification sent to user {user_id}")
                    return True
                else:
                    logger.warning(
                        f"Failed to send notification to user {user_id}: "
                        f"Status {response.status_code}, Response: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            return False

    @staticmethod
    async def notify_payment_received(
        user_id: int,
        amount_usd: Decimal,
        new_balance: Decimal,
        payment_uuid: Optional[str] = None
    ) -> bool:
        """
        Send notification about successful payment.

        Args:
            user_id: Telegram user ID
            amount_usd: Payment amount in USD
            new_balance: User's new balance after payment
            payment_uuid: Optional payment UUID for reference

        Returns:
            True if notification sent successfully
        """
        message = (
            f"✅ <b>Баланс пополнен!</b>\n\n"
            f"💰 Сумма: <code>${amount_usd:.2f}</code>\n"
            f"💵 Новый баланс: <code>${new_balance:.2f}</code>"
        )

        if payment_uuid:
            message += f"\n🆔 ID платежа: <code>{payment_uuid[:16]}...</code>"

        return await NotificationService.send_telegram_message(user_id, message)

    @staticmethod
    async def notify_purchase_success(
        user_id: int,
        product_type: str,
        price: Decimal,
        new_balance: Decimal,
        details: Optional[str] = None
    ) -> bool:
        """
        Send notification about successful purchase.

        Args:
            user_id: Telegram user ID
            product_type: Type of purchased product (SOCKS5, PPTP, etc.)
            price: Purchase price
            new_balance: User's new balance after purchase
            details: Optional purchase details

        Returns:
            True if notification sent successfully
        """
        message = (
            f"🛒 <b>Покупка совершена!</b>\n\n"
            f"📦 Тип: {product_type}\n"
            f"💲 Цена: <code>${price:.2f}</code>\n"
            f"💵 Остаток: <code>${new_balance:.2f}</code>"
        )

        if details:
            message += f"\n\n{details}"

        return await NotificationService.send_telegram_message(user_id, message)

    @staticmethod
    async def notify_refund(
        user_id: int,
        amount: Decimal,
        new_balance: Decimal,
        reason: Optional[str] = None
    ) -> bool:
        """
        Send notification about refund.

        Args:
            user_id: Telegram user ID
            amount: Refund amount
            new_balance: User's new balance after refund
            reason: Optional refund reason

        Returns:
            True if notification sent successfully
        """
        message = (
            f"💸 <b>Возврат средств</b>\n\n"
            f"💰 Сумма: <code>${amount:.2f}</code>\n"
            f"💵 Новый баланс: <code>${new_balance:.2f}</code>"
        )

        if reason:
            message += f"\n📝 Причина: {reason}"

        return await NotificationService.send_telegram_message(user_id, message)
