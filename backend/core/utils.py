from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
import json


def calculate_hours_left(expires_at: datetime) -> int:
    """
    Calculate the number of hours remaining until proxy expires.

    Args:
        expires_at: Expiration datetime

    Returns:
        Number of hours remaining (0 if already expired)

    Example:
        >>> from datetime import datetime, timedelta, timezone
        >>> expires = datetime.now(timezone.utc) + timedelta(hours=12)
        >>> hours = calculate_hours_left(expires)
        >>> assert hours == 12
    """
    # Normalize to UTC
    now = datetime.now(timezone.utc)

    # If expires_at is naive, assume UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    delta = expires_at - now

    # If already expired, return 0
    if delta.total_seconds() < 0:
        return 0

    # Return whole hours
    return int(delta.total_seconds() / 3600)


def calculate_minutes_since_purchase(datestamp: datetime) -> int:
    """
    Calculate the number of minutes since purchase.

    Args:
        datestamp: Purchase datetime

    Returns:
        Number of minutes since purchase

    Example:
        >>> from datetime import datetime, timedelta, timezone
        >>> purchase_time = datetime.now(timezone.utc) - timedelta(minutes=45)
        >>> minutes = calculate_minutes_since_purchase(purchase_time)
        >>> assert minutes == 45
    """
    # Normalize to UTC
    now = datetime.now(timezone.utc)

    # If datestamp is naive, assume UTC
    if datestamp.tzinfo is None:
        datestamp = datestamp.replace(tzinfo=timezone.utc)

    delta = now - datestamp
    return int(delta.total_seconds() / 60)


def is_refund_eligible(datestamp: datetime, refund_window_minutes: int) -> bool:
    """
    Check if proxy is eligible for refund based on purchase time.

    Args:
        datestamp: Purchase datetime
        refund_window_minutes: Refund window in minutes (30 for SOCKS5, 1440 for PPTP)

    Returns:
        True if within refund window, False otherwise

    Example:
        >>> from datetime import datetime, timedelta
        >>> # Purchase 20 minutes ago
        >>> purchase_time = datetime.utcnow() - timedelta(minutes=20)
        >>> # Check with 30 minute window
        >>> eligible = is_refund_eligible(purchase_time, 30)
        >>> assert eligible == True
        >>> # Check with 10 minute window
        >>> not_eligible = is_refund_eligible(purchase_time, 10)
        >>> assert not_eligible == False
    """
    minutes_since = calculate_minutes_since_purchase(datestamp)
    return minutes_since <= refund_window_minutes


def parse_proxy_json(proxy_json: str) -> Dict[str, Any]:
    """
    Safely parse JSON string with proxy data.

    Args:
        proxy_json: JSON string from Product.product or ProxyHistory.proxies

    Returns:
        Parsed dictionary with proxy data, empty dict if parsing fails

    Example:
        >>> data_str = '{"ip": "192.168.1.1", "port": "1080", "login": "user", "password": "pass"}'
        >>> proxy_data = parse_proxy_json(data_str)
        >>> assert proxy_data["ip"] == "192.168.1.1"
        >>> assert proxy_data["port"] == "1080"
    """
    try:
        data = json.loads(proxy_json)

        # Validate required fields for different proxy types
        if "ip" not in data:
            return {}

        # For SOCKS5, check port presence
        if "port" in data and not all(k in data for k in ["login", "password"]):
            return {}

        # For PPTP, check login/password presence
        if "port" not in data and not all(k in data for k in ["login", "password"]):
            return {}

        return data

    except (json.JSONDecodeError, TypeError):
        return {}


def format_proxy_string(proxy_data: Dict[str, Any], proxy_type: str = "socks5") -> str:
    """
    Format proxy data into a readable string.

    Args:
        proxy_data: Dictionary with proxy data
        proxy_type: Type of proxy ("socks5" or "pptp")

    Returns:
        Formatted proxy string

    Example:
        >>> proxy = {"ip": "192.168.1.1", "port": "1080", "login": "user", "password": "pass"}
        >>> formatted = format_proxy_string(proxy, "socks5")
        >>> assert formatted == "192.168.1.1:1080:user:pass"
        >>> pptp = {"ip": "192.168.1.1", "login": "user", "password": "pass", "state": "NY", "city": "New York", "zip": "10001"}
        >>> formatted_pptp = format_proxy_string(pptp, "pptp")
        >>> assert formatted_pptp == "192.168.1.1:user:pass:NY:New York:10001"
    """
    if proxy_type.lower() == "socks5":
        # Format: ip:port:login:password
        return f"{proxy_data.get('ip', '')}:{proxy_data.get('port', '')}:{proxy_data.get('login', '')}:{proxy_data.get('password', '')}"
    else:  # pptp
        # Format: IP:Login:Pass:State:City:Zip (colon-separated)
        return f"{proxy_data.get('ip', '')}:{proxy_data.get('login', '')}:{proxy_data.get('password', '')}:{proxy_data.get('state', '')}:{proxy_data.get('city', '')}:{proxy_data.get('zip', '')}"


# Country code to name mapping for flexible search
# Supports both country codes (US, GB) and full names (United States, United Kingdom)
COUNTRY_CODE_TO_NAME = {
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "DE": "Germany",
    "FR": "France",
    "NL": "Netherlands",
    "IT": "Italy",
    "ES": "Spain",
    "SE": "Sweden",
    "NO": "Norway",
    "FI": "Finland",
    "DK": "Denmark",
    "PL": "Poland",
    "CZ": "Czech Republic",
    "AT": "Austria",
    "CH": "Switzerland",
    "BE": "Belgium",
    "IE": "Ireland",
    "PT": "Portugal",
    "GR": "Greece",
    "RO": "Romania",
    "BG": "Bulgaria",
    "HU": "Hungary",
    "SK": "Slovakia",
    "HR": "Croatia",
    "SI": "Slovenia",
    "LT": "Lithuania",
    "LV": "Latvia",
    "EE": "Estonia",
    "LU": "Luxembourg",
    "MT": "Malta",
    "CY": "Cyprus",
    "JP": "Japan",
    "CN": "China",
    "KR": "South Korea",
    "IN": "India",
    "AU": "Australia",
    "NZ": "New Zealand",
    "SG": "Singapore",
    "HK": "Hong Kong",
    "TW": "Taiwan",
    "TH": "Thailand",
    "MY": "Malaysia",
    "ID": "Indonesia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "BR": "Brazil",
    "MX": "Mexico",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "VE": "Venezuela",
    "ZA": "South Africa",
    "EG": "Egypt",
    "NG": "Nigeria",
    "KE": "Kenya",
    "MA": "Morocco",
    "TN": "Tunisia",
    "DZ": "Algeria",
    "IL": "Israel",
    "TR": "Turkey",
    "SA": "Saudi Arabia",
    "AE": "United Arab Emirates",
    "KW": "Kuwait",
    "QA": "Qatar",
    "OM": "Oman",
    "BH": "Bahrain",
    "JO": "Jordan",
    "LB": "Lebanon",
    "RU": "Russia",
    "UA": "Ukraine",
    "BY": "Belarus",
    "KZ": "Kazakhstan",
    "UZ": "Uzbekistan",
    "GE": "Georgia",
    "AM": "Armenia",
    "AZ": "Azerbaijan",
    "MD": "Moldova",
}


def normalize_country(country: str) -> str:
    """
    Normalize country input to full country name.
    Accepts both country codes (US) and full names (United States).

    Args:
        country: Country code or name

    Returns:
        Full country name (e.g., "United States")
    """
    if not country:
        return country

    # Check if it's a country code (2 letters)
    if len(country) == 2:
        country_upper = country.upper()
        return COUNTRY_CODE_TO_NAME.get(country_upper, country)

    # Otherwise, return as-is (assume it's already a full name)
    return country


def convert_speed_to_category(speed_ms: Optional[str | int]) -> Optional[str]:
    """
    Convert numeric latency (ms) to speed category.

    Args:
        speed_ms: Latency in milliseconds (as string or int)

    Returns:
        "Fast" (<=300ms), "Moderate" (301-600ms), "Slow" (>600ms), or None

    Example:
        >>> convert_speed_to_category("150")
        'Fast'
        >>> convert_speed_to_category(500)
        'Moderate'
        >>> convert_speed_to_category("900")
        'Slow'
        >>> convert_speed_to_category(None)
        None
    """
    if speed_ms is None:
        return None
    try:
        speed = int(speed_ms)
        if speed <= 300:
            return "Fast"
        elif speed <= 600:
            return "Moderate"
        else:
            return "Slow"
    except (ValueError, TypeError):
        return None
