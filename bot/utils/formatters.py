"""Message formatters for bot responses."""
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from aiogram.utils.i18n import gettext as _


def mask_ip_address(ip: str) -> str:
    """
    Mask last 2 octets of IP address for privacy.

    Example: 104.11.157.41 -> 104.11.***.***

    Args:
        ip: IP address string

    Returns:
        Masked IP address
    """
    if not ip:
        return ip
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    return ip


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, handling strings and Decimals.
    
    Args:
        value: Value to convert (can be int, float, str, Decimal, etc.)
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    # Try to convert any other type
    try:
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default


def format_proxy_details(proxy_data: Dict[str, Any]) -> str:
    """Format proxy details for display.

    Args:
        proxy_data: Proxy product data from API

    Returns:
        Formatted message string
    """
    ip = proxy_data.get("ip", "N/A")
    # Use uppercase keys to match API schema (ISP, ORG)
    isp = proxy_data.get("ISP", "N/A")
    org = proxy_data.get("ORG", "N/A")
    city = proxy_data.get("city", "N/A")
    # Use 'state' as fallback for 'region' since API uses 'state' field
    region = proxy_data.get("state", "N/A")
    speed = proxy_data.get("speed", "N/A")
    zip_code = proxy_data.get("zip", "N/A")
    country = proxy_data.get("country", "N/A")

    # Format 'datestamp' field from API
    datestamp = proxy_data.get("datestamp")
    if isinstance(datestamp, datetime):
        added_date = datestamp.strftime("%Y-%m-%d %H:%M")
    elif isinstance(datestamp, str) and datestamp != "N/A":
        try:
            parsed_date = datetime.fromisoformat(datestamp.replace('Z', '+00:00'))
            added_date = parsed_date.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            added_date = datestamp
    else:
        added_date = "N/A"
    
    message = (
        f"🪄 IP <code>{ip}</code>\n"
        f"📡 ISP {isp}\n"
        f"📡 ORG {org}\n"
        f"🏷 {_('Город')} {city}\n"
        f"🏷 {_('Регион')} {region}\n"
        f"🏷 {_('Скорость')} {speed}\n"
        f"🏷 ZIP {zip_code}\n"
        f"📌 {_('Страна')} {country}\n"
        f"📌 {_('Добавлено')} {added_date}"
    )
    
    return message


def format_purchase_success(
    purchase_id: int,
    price: float,
    country: str,
    state: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    proxy_credentials: Optional[str] = None
) -> str:
    """Format successful purchase message.
    
    Args:
        purchase_id: Purchase ID
        price: Price in USD
        country: Country name
        state: State/region name
        city: City name
        zip_code: ZIP code
        proxy_credentials: Proxy connection string
        
    Returns:
        Formatted message string
    """
    price = _safe_float(price)
    
    message = (
        f"{_('Покупка совершена успешно!')}\n\n"
        f"🆔 {_('ID Покупки')}: {purchase_id}\n"
        f"💲 {_('Цена')}: {price:.2f}$\n"
        f"🔖 {_('Страна')}: {country}\n"
    )
    
    if state:
        message += f"🗽 {_('Штат')}: {state}\n"
    if city:
        message += f"🗽 {_('Город')}: {city}\n"
    if zip_code:
        message += f"📬 {_('ЗИП')}: {zip_code}\n"
    
    if proxy_credentials:
        message += f"\n🔑 {_('Прокси')}: <code>{proxy_credentials}</code>"
    
    return message


def format_deposit_success(
    currency: str,
    coin_amount: float,
    usdt_amount: float,
    txid: str,
    date: str,
    new_balance: float
) -> str:
    """Format successful deposit notification.
    
    Args:
        currency: Cryptocurrency (BTC, ETH, etc.)
        coin_amount: Amount in cryptocurrency
        usdt_amount: Amount in USD
        txid: Transaction ID
        date: Transaction date
        new_balance: New account balance
        
    Returns:
        Formatted message string
    """
    coin_amount = _safe_float(coin_amount)
    usdt_amount = _safe_float(usdt_amount)
    new_balance = _safe_float(new_balance)
    
    message = (
        f"🥳 {_('Your payment was successful')}\n\n"
        f"🧾 {_('Information about the deposit')}\n\n"
        f"{_('Currency')}: {currency}\n\n"
        f"{currency} {_('amount')}: {coin_amount} {currency}\n"
        f"USDT {_('amount')}: {usdt_amount}$\n\n"
        f"TXID: {txid}\n"
        f"{_('Date of replenishment')}: {date} (GMT 0)\n\n"
        f"💸 {_('Balance')}: {new_balance} $"
    )
    
    return message


def format_user_profile(profile_data: Dict[str, Any]) -> str:
    """Format user profile for display.
    
    Args:
        profile_data: User profile data from API (UserProfileResponse schema)
        
    Returns:
        Formatted message string in HTML format
    """
    # Map fields from UserProfileResponse schema
    user_id = profile_data.get("user_id", "N/A")
    access_code = profile_data.get("access_code", "N/A")
    balance = _safe_float(profile_data.get("balance", 0.0))
    datestamp = profile_data.get("datestamp", "N/A")
    referal_quantity = profile_data.get("referal_quantity", 0)
    referral_link_bot = profile_data.get("referral_link_bot", "N/A")
    referral_link_web = profile_data.get("referral_link_web", "N/A")
    
    # Format datestamp to human-readable string if it's a datetime object
    if isinstance(datestamp, datetime):
        reg_date = datestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(datestamp, str) and datestamp != "N/A":
        # If it's already a string, try to parse and reformat
        try:
            parsed_date = datetime.fromisoformat(datestamp.replace('Z', '+00:00'))
            reg_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            reg_date = datestamp
    else:
        reg_date = datestamp
    
    from bot.core.config import bot_settings
    
    message = (
        f"👤 {_('АККАУНТ')}\n\n"
        f"<b>Acc Id:</b> <code>{user_id}</code>\n"
        f"<b>{_('Код доступа')}:</b> <code>{access_code}</code>\n"
        f"<b>Balance:</b> <code>{balance:.2f}$</code>\n"
        f"<b>Reg date:</b> <code>{reg_date}</code>\n"
        f"<b>Ref link:</b> <code>{referral_link_bot}</code>\n"
        f"<b>Referrals:</b> <code>{referal_quantity}</code>\n\n"
        f"💡 <i>{_('Используйте этот код для входа на веб-сайте и в админ-панели')}</i>\n\n"
        f"<b>Telegram links USE.NET</b>\n"
        f"- 📢 <a href=\"{bot_settings.NEWS_CHANNEL_URL}\"><b>{_('Канал')}</b></a>\n"
        f"- 🪞 <a href=\"{bot_settings.MIRROR_CHANNEL_URL}\"><b>{_('Зеркало')}</b></a>\n"
        f"- 📜 <a href=\"{bot_settings.RULES_URL}\"><b>{_('Правила')}</b></a>\n"
        f"- 💬 <a href=\"https://t.me/shop_pptp\"><b>{_('Поддержка')}</b></a>"
    )
    
    return message


def format_history_entry(
    action_type: str,
    amount: float,
    timestamp: str
) -> str:
    """Format single history entry.
    
    Args:
        action_type: Type of action (DEPOSIT, BUY Socks5, BUY PPTP)
        amount: Amount in USD
        timestamp: Timestamp string
        
    Returns:
        Formatted history line
    """
    amount = _safe_float(amount)
    return f"{action_type} {amount:.1f} 🕞{timestamp}"


def format_payment_invoice(
    payment_url: str,
    order_id: str,
    amount_usd: float,
    min_amount_usd: float,
    expired_at: Optional[str] = None
) -> str:
    """Format Heleket payment invoice details for display.
    
    Args:
        payment_url: Universal payment link
        order_id: Order/invoice ID
        amount_usd: Invoice amount in USD (should not be None after handling in caller)
        min_amount_usd: Minimum deposit amount (should not be None after handling in caller)
        expired_at: Expiration timestamp (ISO format)
        
    Returns:
        Formatted message string
    """
    # Convert to float safely
    amount_usd = _safe_float(amount_usd)
    min_amount_usd = _safe_float(min_amount_usd)
    
    message = (
        f"💰 <b>{_('Пополнение баланса')}</b>\n\n"
        f"💵 {_('Сумма')}: {amount_usd:.2f}$\n"
        f"🆔 {_('Номер заказа')}: <code>{order_id}</code>\n"
    )
    
    if expired_at:
        message += f"⏰ {_('Действителен до')}: {expired_at}\n"
    
    message += (
        f"\n‼️ {_('Минимальное пополнение')}: {min_amount_usd:.2f}$\n\n"
        f"👇 {_('Нажмите кнопку ниже для перехода к оплате')}\n"
        f"ℹ️ {_('На странице оплаты вы сможете выбрать любую поддерживаемую криптовалюту')}"
    )
    
    return message


def format_payment_address(
    chain: str,
    address: str,
    network_name: str,
    min_deposit: float,
    valid_until: Optional[str] = None
) -> str:
    """Format payment address message.
    
    DEPRECATED: This function is for legacy transaction history display only.
    New deposits use Heleket universal payment links (see format_payment_invoice).
    
    Args:
        chain: Blockchain chain code
        address: Payment address
        network_name: Human-readable network name
        min_deposit: Minimum deposit amount
        valid_until: Address expiration datetime (for USDT_TRC20)
        
    Returns:
        Formatted message string
    """
    min_deposit = _safe_float(min_deposit)
    
    message = (
        f"‼️ {_('Минимальное пополнение')}: {min_deposit}$\n\n"
        f"💲 {_('Монета')}: {chain}\n"
        f"❗️ {_('Сеть')}: {network_name}\n\n"
        f"➡️ {_('Адрес')}: `{address}`\n\n"
    )
    
    if valid_until:
        message += f"⏰ {_('Действителен до')}: {valid_until}\n\n"
    
    message += f"ℹ️ {_('Вы можете отсканировать qr что бы автоматически вставить адрес, но при этом рекомендуется все равно перепроверить все.')}"
    
    return message


def format_proxy_validation_result(
    is_online: bool,
    time_since_purchase: Optional[str] = None,
    can_refund: bool = False
) -> str:
    """Format proxy validation result message.
    
    Args:
        is_online: Whether proxy is online
        time_since_purchase: Time elapsed since purchase
        can_refund: Whether refund is available
        
    Returns:
        Formatted message string
    """
    if is_online:
        return f"✅ {_('Прокси онлайн!')}"
    else:
        message = f"❌ {_('Прокси офлайн!')}"
        if time_since_purchase:
            message += f" {_('С момента покупки прошло')} {time_since_purchase}."
        if can_refund:
            message += f" → {_('REFOUND')}"
        elif time_since_purchase:
            message += f" → {_('GARANTY GONE')}"
        return message


def format_pptp_info(
    pptp_data: Dict[str, Any],
    state: str,
    price: float
) -> str:
    """Format PPTP proxy information.
    
    Args:
        pptp_data: PPTP product data
        state: State name (or RANDOM)
        price: Price in USD
        
    Returns:
        Formatted message string
    """
    region = pptp_data.get("region", "US")
    price = _safe_float(price)
    
    message = (
        f"🔐 PPTP {region} state[{state}]\n"
        f"💲 {_('price')}: {price:.2f}$"
    )
    
    return message


def format_no_results_message(filter_type: str) -> str:
    """Format 'no results found' message based on filter type.
    
    Args:
        filter_type: Type of filter (state/city/zip)
        
    Returns:
        Formatted message string
    """
    messages = {
        "state": _("Данного региона нет в списке прокси"),
        "city": _("К сожалению в списке прокси текущего города нет.\nПопробуйте ближайший прокси или другие настройки."),
        "zip": _("К сожалению в списке прокси текущего ZIP нет.\nПопробуйте ближайший прокси или другие настройки."),
    }
    
    return messages.get(filter_type, _("Результатов не найдено"))


def format_zip_list(zip_codes: list[str]) -> str:
    """Format list of ZIP codes.
    
    Args:
        zip_codes: List of ZIP codes
        
    Returns:
        Formatted message string
    """
    if not zip_codes:
        return _("ZIP коды недоступны")
    
    zip_string = ", ".join(zip_codes)
    return f"{_('Доступные ZIP коды')}:\n\n{zip_string}"
