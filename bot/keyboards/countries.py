"""Country selection keyboard builders."""
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from bot.keyboards.callback_data import CountryCallback, PaginationCallback, MenuCallback


# Country list with flags (organized by pages as per architecture)
COUNTRIES_PAGE_1 = [
    ("🇺🇸", "US", "США"),
    ("🇬🇧", "GB", "Великобритания"),
    ("🇨🇦", "CA", "Канада"),
    ("🇩🇪", "DE", "Германия"),
    ("🇫🇷", "FR", "Франция"),
    ("🇳🇱", "NL", "Нидерланды"),
    ("🇦🇺", "AU", "Австралия"),
    ("🇯🇵", "JP", "Япония"),
    ("🇰🇷", "KR", "Южная Корея"),
    ("🇨🇭", "CH", "Швейцария"),
    ("🇸🇬", "SG", "Сингапур"),
    ("🇮🇪", "IE", "Ирландия"),
    ("🇸🇪", "SE", "Швеция"),
    ("🇩🇰", "DK", "Дания"),
    ("🇳🇴", "NO", "Норвегия"),
]

COUNTRIES_PAGE_2 = [
    ("🇮🇹", "IT", "Италия"),
    ("🇪🇸", "ES", "Испания"),
    ("🇵🇹", "PT", "Португалия"),
    ("🇧🇪", "BE", "Бельгия"),
    ("🇦🇹", "AT", "Австрия"),
    ("🇨🇿", "CZ", "Чехия"),
    ("🇵🇱", "PL", "Польша"),
    ("🇬🇷", "GR", "Греция"),
    ("🇭🇺", "HU", "Венгрия"),
    ("🇫🇮", "FI", "Финляндия"),
    ("🇱🇹", "LT", "Литва"),
    ("🇱🇻", "LV", "Латвия"),
    ("🇪🇪", "EE", "Эстония"),
    ("🇮🇱", "IL", "Израиль"),
    ("🇦🇪", "AE", "ОАЭ"),
]

COUNTRIES_PAGE_3 = [
    ("🇲🇽", "MX", "Мексика"),
    ("🇧🇷", "BR", "Бразилия"),
    ("🇦🇷", "AR", "Аргентина"),
    ("🇨🇱", "CL", "Чили"),
    ("🇨🇴", "CO", "Колумбия"),
    ("🇵🇪", "PE", "Перу"),
    ("🇮🇳", "IN", "Индия"),
    ("🇮🇩", "ID", "Индонезия"),
    ("🇲🇾", "MY", "Малайзия"),
    ("🇹🇭", "TH", "Таиланд"),
    ("🇻🇳", "VN", "Вьетнам"),
    ("🇵🇭", "PH", "Филиппины"),
    ("🇿🇦", "ZA", "Южная Африка"),
    ("🇹🇷", "TR", "Турция"),
    ("🇸🇦", "SA", "Саудовская Аравия"),
]

COUNTRIES_PAGE_4 = [
    ("🇰🇼", "KW", "Кувейт"),
    ("🇶🇦", "QA", "Катар"),
    ("🇳🇿", "NZ", "Новая Зеландия"),
    ("🇭🇰", "HK", "Гонконг"),
    ("🇹🇼", "TW", "Тайвань"),
]

ALL_COUNTRIES = [COUNTRIES_PAGE_1, COUNTRIES_PAGE_2, COUNTRIES_PAGE_3, COUNTRIES_PAGE_4]


def build_countries_keyboard(
    proxy_type: str,  # "socks5" or "pptp"
    page: int = 1
) -> InlineKeyboardMarkup:
    """Build country selection keyboard with pagination.
    
    Args:
        proxy_type: Type of proxy (socks5 or pptp)
        page: Current page number (1-4)
        
    Returns:
        InlineKeyboardMarkup with country buttons
    """
    if page < 1 or page > 4:
        page = 1
    
    countries = ALL_COUNTRIES[page - 1]
    
    # Build country buttons (2 per row)
    keyboard = []
    for i in range(0, len(countries), 2):
        row = []
        for j in range(2):
            if i + j < len(countries):
                flag, code, name = countries[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{flag} {name}",
                    callback_data=CountryCallback(
                        proxy_type=proxy_type,
                        country_code=code,
                        page=page
                    ).pack()
                ))
        keyboard.append(row)
    
    # Pagination buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(
            text=_("◀️ Назад"),
            callback_data=PaginationCallback(
                page_type="countries",
                page=page - 1,
                extra=proxy_type
            ).pack()
        ))
    
    nav_row.append(InlineKeyboardButton(
        text=f"{page}/4",
        callback_data="page_info"
    ))
    
    if page < 4:
        nav_row.append(InlineKeyboardButton(
            text=_("Вперед ▶️"),
            callback_data=PaginationCallback(
                page_type="countries",
                page=page + 1,
                extra=proxy_type
            ).pack()
        ))
    
    keyboard.append(nav_row)
    
    # Back to menu button
    keyboard.append([InlineKeyboardButton(
        text=_("🏠 ГЛАВНОЕ МЕНЮ"),
        callback_data=MenuCallback(action="back").pack()
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_country_name(country_code: str) -> str:
    """Get country name by country code.
    
    Args:
        country_code: Two-letter country code
        
    Returns:
        Country name in Russian
    """
    for page in ALL_COUNTRIES:
        for flag, code, name in page:
            if code == country_code:
                return name
    return country_code


def get_country_flag(country_code: str) -> str:
    """Get country flag emoji by country code.
    
    Args:
        country_code: Two-letter country code
        
    Returns:
        Flag emoji
    """
    for page in ALL_COUNTRIES:
        for flag, code, name in page:
            if code == country_code:
                return flag
    return "🏳️"
