"""Payment and deposit keyboard builders."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from bot.keyboards.callback_data import PaymentCallback, AccountCallback


def build_payment_invoice_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Build keyboard with payment URL button for Heleket invoice.

    Args:
        payment_url: Universal payment link from Heleket

    Returns:
        InlineKeyboardMarkup with payment URL and back buttons
    """
    keyboard = [
        [InlineKeyboardButton(
            text=_("💳 Перейти к оплате"),
            url=payment_url
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=AccountCallback(action="back").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_deposit_amount_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for deposit amount input with cancel button.

    Returns:
        InlineKeyboardMarkup with cancel button
    """
    keyboard = [
        [InlineKeyboardButton(
            text=_("◀️ Отмена"),
            callback_data=AccountCallback(action="cancel_deposit").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_insufficient_balance_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for insufficient balance error with deposit button.

    Returns:
        InlineKeyboardMarkup with deposit and back buttons
    """
    from bot.keyboards.callback_data import MenuCallback

    keyboard = [
        [InlineKeyboardButton(
            text=_("💰 ПОПОЛНИТЬ БАЛАНС"),
            callback_data=AccountCallback(action="deposit").pack()
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=MenuCallback(action="back").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

