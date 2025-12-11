"""Callback data factories for inline keyboards."""
from typing import Optional
from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):
    """Main menu navigation callback."""
    action: str  # account, socks5, pptp, support, rules, back


class AccountCallback(CallbackData, prefix="account"):
    """Account-related actions callback."""
    action: str  # deposit, history, login_by_key, my_users, add_user, remove_user, confirm_remove_user, back


class PaymentCallback(CallbackData, prefix="payment"):
    """Payment and deposit callback."""
    action: str  # select_chain, back
    chain: Optional[str] = None  # BTC, ETH, USDT_TRC20, etc.


class CountryCallback(CallbackData, prefix="country"):
    """Country selection callback."""
    proxy_type: str  # socks5 or pptp
    country_code: str  # US, GB, CA, etc.
    page: int = 1  # For pagination


class FilterCallback(CallbackData, prefix="filter"):
    """Proxy filter selection callback."""
    proxy_type: str  # socks5 or pptp
    filter_type: str  # state, city, zip, random, back, back_to_states
    country_code: Optional[str] = None
    state_name: Optional[str] = None


class ProxyCallback(CallbackData, prefix="proxy"):
    """Individual proxy action callback."""
    action: str  # buy, show_more, validate, extend, back
    proxy_id: Optional[int] = None
    page: int = 1


class HistoryCallback(CallbackData, prefix="history"):
    """History navigation callback."""
    history_type: str  # socks5, pptp, account, back
    page: int = 1


class ConfirmCallback(CallbackData, prefix="confirm"):
    """Confirmation action callback."""
    action: str  # yes, no, cancel
    target: str  # purchase_socks5, purchase_pptp, extend_proxy, etc.
    target_id: Optional[int] = None


class PaginationCallback(CallbackData, prefix="page"):
    """Generic pagination callback."""
    page_type: str  # countries, proxies, states, history
    page: int
    extra: Optional[str] = None  # Additional context data


class PPTPRegionCallback(CallbackData, prefix="pptp_region"):
    """PPTP region selection callback."""
    region: str  # USA, EUROPE


class StateSelectionCallback(CallbackData, prefix="state_select"):
    """State/region selection for PPTP and SOCKS5."""
    proxy_type: str  # pptp or socks5
    country_code: str
    state_name: str


class CitySelectionCallback(CallbackData, prefix="city_select"):
    """City selection for SOCKS5."""
    proxy_type: str  # socks5
    country_code: str
    state_name: str
    city_name: str


class ExpandProxiesCallback(CallbackData, prefix="expand"):
    """Expand proxy list callback."""
    quantity: int  # 25, 50, 100
    current_page: int


class ManageUsersCallback(CallbackData, prefix="manage_users"):
    """Manage linked users callback."""
    action: str  # list, add, remove, confirm_remove, cancel
    telegram_id: Optional[int] = None


class CatalogSelectionCallback(CallbackData, prefix="catalog_select"):
    """Catalog selection for PPTP."""
    proxy_type: str  # pptp
    catalog_id: int
    catalog_name: str
    price: str


class PPTPListCallback(CallbackData, prefix="pptp_list"):
    """PPTP list browsing callback."""
    catalog_id: int
    action: str  # show_list, next_page, prev_page, select_proxy
    page: int = 1
    proxy_id: Optional[int] = None
