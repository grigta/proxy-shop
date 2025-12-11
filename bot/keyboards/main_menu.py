"""Main menu keyboard builder."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from bot.keyboards.callback_data import MenuCallback, FilterCallback


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main menu keyboard with primary navigation options.
    
    Returns:
        InlineKeyboardMarkup with menu buttons
    """
    keyboard = [
        [InlineKeyboardButton(
            text=_("👤 АККАУНТ"),
            callback_data=MenuCallback(action="account").pack()
        )],
        [InlineKeyboardButton(
            text=_("🧦 SOCKS5"),
            callback_data=MenuCallback(action="socks5").pack()
        )],
        [InlineKeyboardButton(
            text=_("🔐 PPTP"),
            callback_data=MenuCallback(action="pptp").pack()
        )],
        [InlineKeyboardButton(
            text=_("📜 ПРАВИЛА"),
            callback_data=MenuCallback(action="rules").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with single 'Back to Main Menu' button.

    Returns:
        InlineKeyboardMarkup with back button
    """
    keyboard = [
        [InlineKeyboardButton(
            text=_("🏠 ГЛАВНОЕ МЕНЮ"),
            callback_data=MenuCallback(action="back").pack()
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_purchase_success_keyboard(country_code: str) -> InlineKeyboardMarkup:
    """Build keyboard for successful purchase with Main Menu and Back buttons.

    Args:
        country_code: Country code to return to filter selection

    Returns:
        InlineKeyboardMarkup with main menu and back buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🏠 ГЛАВНОЕ МЕНЮ"),
                callback_data=MenuCallback(action="back").pack()
            ),
            InlineKeyboardButton(
                text=_("◀ НАЗАД"),
                callback_data=FilterCallback(
                    proxy_type="socks5",
                    filter_type="back_to_filter",
                    country_code=country_code
                ).pack()
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
