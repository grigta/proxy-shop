"""Proxy listing and action keyboard builders."""
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from bot.core.config import bot_settings
from bot.keyboards.callback_data import (
    ProxyCallback, FilterCallback, ExpandProxiesCallback,
    StateSelectionCallback, MenuCallback, CountryCallback
)


def build_filter_selection_keyboard(
    proxy_type: str,  # "socks5" or "pptp"
    country_code: str
) -> InlineKeyboardMarkup:
    """Build filter type selection keyboard (state/city/zip/random).

    Args:
        proxy_type: Type of proxy
        country_code: Selected country code

    Returns:
        InlineKeyboardMarkup with filter options
    """
    # For USA: ШТАТ, for others: РЕГИОН
    state_label = _("🗽 ШТАТ") if country_code == "US" else _("🌍 РЕГИОН")

    keyboard = [
        [InlineKeyboardButton(
            text=state_label,
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="state",
                country_code=country_code
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("🏙 ГОРОД"),
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="city",
                country_code=country_code
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("📮 ZIP"),
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="zip",
                country_code=country_code
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("🎲 РАНДОМ"),
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="random",
                country_code=country_code
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("⏭ ПРОПУСТИТЬ ФИЛЬТР"),
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="skip",
                country_code=country_code
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=FilterCallback(
                proxy_type=proxy_type,
                filter_type="back",
                country_code=country_code
            ).pack()
        )],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_proxy_purchase_keyboard(proxy_id: int, price: float = 2.0) -> InlineKeyboardMarkup:
    """Build keyboard for individual proxy with purchase button.

    Args:
        proxy_id: ID of the proxy product
        price: Price in USD

    Returns:
        InlineKeyboardMarkup with buy button
    """
    # Convert price to float if it's a string or Decimal
    try:
        price_float = float(price)
    except (ValueError, TypeError):
        price_float = 2.0

    keyboard = [
        [InlineKeyboardButton(
            text=f"💳 КУПИТЬ ПРОКСИ - {price_float:.2f}$",
            callback_data=ProxyCallback(action="buy", proxy_id=proxy_id).pack()
        )],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_proxy_pagination_keyboard(
    page: int,
    has_more: bool,
    show_expand: bool = False  # Disabled until handlers are implemented
) -> InlineKeyboardMarkup:
    """Build pagination keyboard for proxy listings.
    
    Args:
        page: Current page number
        has_more: Whether there are more proxies to show
        show_expand: Whether to show expand quantity buttons
        
    Returns:
        InlineKeyboardMarkup with pagination
    """
    keyboard = []
    
    if has_more:
        keyboard.append([InlineKeyboardButton(
            text=_("📋 ПОКАЗАТЬ ЕЩЕ 10"),
            callback_data=ProxyCallback(action="show_more", page=page + 1).pack()
        )])
    
    if show_expand:
        expand_row = []
        for qty in bot_settings.EXPAND_PROXIES_OPTIONS:
            expand_row.append(InlineKeyboardButton(
                text=f"+{qty}",
                callback_data=ExpandProxiesCallback(
                    quantity=qty,
                    current_page=page
                ).pack()
            ))
        keyboard.append(expand_row)
    
    keyboard.append([InlineKeyboardButton(
        text=_("◀️ НАЗАД"),
        callback_data=ProxyCallback(action="back").pack()
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_proxy_history_actions_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for proxy history actions (validate/extend).
    
    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = [
        [InlineKeyboardButton(
            text=_("✅ ПРОВЕРКА НА ВАЛИД"),
            callback_data=ProxyCallback(action="validate").pack()
        )],
        [InlineKeyboardButton(
            text=_("🔄 ПРОДЛИТЬ ПРОКСИ"),
            callback_data=ProxyCallback(action="extend").pack()
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=ProxyCallback(action="back").pack()
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_states_list_keyboard(
    proxy_type: str,
    country_code: str,
    states: List[Dict[str, Any]]
) -> InlineKeyboardMarkup:
    """Build keyboard with list of states for selection.

    Shows all states with abbreviation and available proxy count.
    Format: "CA | 77" (abbreviation | count)

    Args:
        proxy_type: Type of proxy
        country_code: Country code
        states: List of state dicts with keys: state, abbr, count

    Returns:
        InlineKeyboardMarkup with state buttons (3 per row)
    """
    keyboard = []

    # Add state buttons (3 per row)
    for i in range(0, len(states), 3):
        row = []
        for j in range(3):
            if i + j < len(states):
                state_data = states[i + j]
                state_name = state_data.get("state", "")
                abbr = state_data.get("abbr", state_name[:2].upper())
                count = state_data.get("count", 0)

                row.append(InlineKeyboardButton(
                    text=f"{abbr} | {count}",
                    callback_data=StateSelectionCallback(
                        proxy_type=proxy_type,
                        country_code=country_code,
                        state_name=state_name
                    ).pack()
                ))
        keyboard.append(row)

    # Back button
    keyboard.append([InlineKeyboardButton(
        text=_("◀️ НАЗАД"),
        callback_data=FilterCallback(
            proxy_type=proxy_type,
            filter_type="back",
            country_code=country_code
        ).pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_cities_list_keyboard(
    proxy_type: str,
    country_code: str,
    state_name: str,
    cities: List[str]
) -> InlineKeyboardMarkup:
    """Build keyboard with list of cities for selection.

    Args:
        proxy_type: Type of proxy
        country_code: Country code
        state_name: State/region name
        cities: List of city names

    Returns:
        InlineKeyboardMarkup with city buttons
    """
    from bot.keyboards.callback_data import CitySelectionCallback, StateSelectionCallback

    keyboard = []

    # Add city buttons (2 per row)
    for i in range(0, len(cities), 2):
        row = []
        for j in range(2):
            if i + j < len(cities):
                city = cities[i + j]
                row.append(InlineKeyboardButton(
                    text=city,
                    callback_data=CitySelectionCallback(
                        proxy_type=proxy_type,
                        country_code=country_code,
                        state_name=state_name,
                        city_name=city
                    ).pack()
                ))
        keyboard.append(row)

    # Back button - go back to states list
    keyboard.append([InlineKeyboardButton(
        text=_("◀️ НАЗАД"),
        callback_data=FilterCallback(
            proxy_type=proxy_type,
            filter_type="back_to_states",
            country_code=country_code,
            state_name=state_name
        ).pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_zip_list_keyboard(zip_codes: List[str]) -> InlineKeyboardMarkup:
    """Build keyboard showing all available ZIP codes.
    
    Args:
        zip_codes: List of ZIP codes
        
    Returns:
        InlineKeyboardMarkup with back button
    """
    # ZIP codes are shown in message text, not as buttons
    keyboard = [
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=ProxyCallback(action="back").pack()
        )],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_pptp_region_keyboard() -> InlineKeyboardMarkup:
    """Build PPTP region selection keyboard (USA/EUROPE).

    Returns:
        InlineKeyboardMarkup with region buttons
    """
    from bot.keyboards.callback_data import PPTPRegionCallback

    keyboard = [
        [InlineKeyboardButton(
            text=_("🇺🇸 USA"),
            callback_data=PPTPRegionCallback(region="USA").pack()
        )],
        [InlineKeyboardButton(
            text=_("🇪🇺 EUROPE"),
            callback_data=PPTPRegionCallback(region="EUROPE").pack()
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=MenuCallback(action="back").pack()
        )],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_catalogs_list_keyboard(catalogs: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Build catalog selection keyboard with 2 catalogs per row.

    Args:
        catalogs: List of catalog dicts with id, name, price, product_count

    Returns:
        InlineKeyboardMarkup with catalog buttons
    """
    from bot.keyboards.callback_data import CatalogSelectionCallback

    keyboard = []

    # Add catalogs 2 per row
    for i in range(0, len(catalogs), 2):
        row = []
        for j in range(2):
            if i + j < len(catalogs):
                cat = catalogs[i + j]
                button_text = f"📦 {cat['name']} - ${cat['price']:.2f}"
                row.append(InlineKeyboardButton(
                    text=button_text,
                    callback_data=CatalogSelectionCallback(
                        proxy_type="pptp",
                        catalog_id=cat['id'],
                        catalog_name=cat['name'],
                        price=str(cat['price'])
                    ).pack()
                ))
        keyboard.append(row)

    # Back button
    keyboard.append([InlineKeyboardButton(
        text=_("◀️ НАЗАД"),
        callback_data=MenuCallback(action="back").pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_pptp_list_keyboard(
    proxies: List[Dict[str, Any]],
    catalog_id: int,
    page: int,
    total: int,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    """Build PPTP proxy list keyboard with pagination.

    Args:
        proxies: List of proxy dicts with product_id, ip, state, city
        catalog_id: Current catalog ID
        page: Current page number
        total: Total number of proxies
        page_size: Items per page

    Returns:
        InlineKeyboardMarkup with proxy buttons and pagination
    """
    from bot.keyboards.callback_data import PPTPListCallback

    keyboard = []

    # Add proxy buttons (one per row)
    from bot.utils.formatters import mask_ip_address
    for proxy in proxies:
        location = f"{proxy.get('state', '')} - {proxy.get('city', '')}".strip(' -')
        masked_ip = mask_ip_address(proxy['ip'])
        button_text = f"🔐 {masked_ip} • {location}"
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=PPTPListCallback(
                catalog_id=catalog_id,
                action="select_proxy",
                page=page,
                proxy_id=proxy['product_id']
            ).pack()
        )])

    # Pagination buttons
    has_prev = page > 1
    has_next = (page * page_size) < total

    if has_prev or has_next:
        pagination_row = []

        if has_prev:
            pagination_row.append(InlineKeyboardButton(
                text=_("⬅️ Назад"),
                callback_data=PPTPListCallback(
                    catalog_id=catalog_id,
                    action="prev_page",
                    page=page - 1
                ).pack()
            ))

        # Page indicator
        pagination_row.append(InlineKeyboardButton(
            text=f"📄 {page}",
            callback_data=PPTPListCallback(
                catalog_id=catalog_id,
                action="show_list",
                page=page
            ).pack()
        ))

        if has_next:
            pagination_row.append(InlineKeyboardButton(
                text=_("Вперед ➡️"),
                callback_data=PPTPListCallback(
                    catalog_id=catalog_id,
                    action="next_page",
                    page=page + 1
                ).pack()
            ))

        keyboard.append(pagination_row)

    # Back to catalog selection
    keyboard.append([InlineKeyboardButton(
        text=_("◀️ НАЗАД К КАТАЛОГАМ"),
        callback_data=MenuCallback(action="pptp").pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
