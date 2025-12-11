"""Input validators for bot handlers."""
import re
from typing import Optional, Tuple


def validate_proxy_id(text: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validate proxy ID input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (is_valid, proxy_id, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, None, "ID прокси не может быть пустым"
    
    if not text.isdigit():
        return False, None, "ID прокси должен быть числом"
    
    proxy_id = int(text)
    
    if proxy_id <= 0:
        return False, None, "ID прокси должен быть положительным числом"
    
    return True, proxy_id, None


def validate_state_name(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate state/region name input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (is_valid, state_name, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, None, "Название штата/региона не может быть пустым"
    
    if len(text) < 2:
        return False, None, "Название штата/региона слишком короткое"
    
    if len(text) > 100:
        return False, None, "Название штата/региона слишком длинное"
    
    # Allow letters, spaces, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$", text):
        return False, None, "Название штата/региона содержит недопустимые символы"
    
    return True, text, None


def validate_city_name(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate city name input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (is_valid, city_name, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, None, "Название города не может быть пустым"
    
    if len(text) < 2:
        return False, None, "Название города слишком короткое"
    
    if len(text) > 100:
        return False, None, "Название города слишком длинное"
    
    # Allow letters, spaces, hyphens, apostrophes, and dots
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-'.]+$", text):
        return False, None, "Название города содержит недопустимые символы"
    
    return True, text, None


def validate_zip_code(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate ZIP code input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (is_valid, zip_code, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, None, "ZIP код не может быть пустым"
    
    # Most ZIP codes are 3-10 characters
    if len(text) < 3 or len(text) > 10:
        return False, None, "Неверный формат ZIP кода"
    
    # Allow digits, letters, spaces, and hyphens
    if not re.match(r"^[a-zA-Z0-9\s\-]+$", text):
        return False, None, "ZIP код содержит недопустимые символы"
    
    return True, text, None


def validate_ip_address(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate IP address input.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (is_valid, ip_address, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, None, "IP адрес не может быть пустым"
    
    # Simple IPv4 validation
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(ipv4_pattern, text):
        return False, None, "Неверный формат IP адреса"
    
    # Validate each octet is 0-255
    octets = text.split(".")
    for octet in octets:
        try:
            val = int(octet)
            if val < 0 or val > 255:
                return False, None, "IP адрес содержит недопустимые значения"
        except ValueError:
            return False, None, "Неверный формат IP адреса"
    
    return True, text, None


def sanitize_text_input(text: str, max_length: int = 500) -> str:
    """Sanitize and truncate text input.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    # Remove leading/trailing whitespace
    text = text.strip()

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    return text


def validate_access_code(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate access code format (XXX-XXX-XXX).

    Args:
        text: User input text

    Returns:
        Tuple of (is_valid, normalized_code, error_message)
    """
    text = text.strip().upper()

    if not text:
        return False, None, "Код доступа не может быть пустым"

    # Check length (11 characters including dashes)
    if len(text) != 11:
        return False, None, "Код должен быть длиной 11 символов (включая дефисы)"

    # Check format XXX-XXX-XXX
    if not re.match(r"^[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}$", text):
        return False, None, "Неверный формат. Используйте формат XXX-XXX-XXX"

    # Additional check - only alphanumeric
    code_without_dashes = text.replace("-", "")
    if not code_without_dashes.isalnum():
        return False, None, "Код должен содержать только буквы и цифры"

    return True, text, None


def validate_telegram_id(text: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validate Telegram ID (must be positive integer).

    Args:
        text: User input text

    Returns:
        Tuple of (is_valid, telegram_id, error_message)
    """
    text = text.strip()

    if not text:
        return False, None, "Telegram ID не может быть пустым"

    if not text.isdigit():
        return False, None, "Telegram ID должен быть числом"

    try:
        telegram_id = int(text)
    except ValueError:
        return False, None, "Неверный формат Telegram ID"

    if telegram_id <= 0:
        return False, None, "Telegram ID должен быть положительным числом"

    return True, telegram_id, None
