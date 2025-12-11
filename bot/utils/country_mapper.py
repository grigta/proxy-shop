"""
Модуль для конвертации кодов стран в полные названия.

Решает проблему несоответствия между кодами стран, используемыми в боте (US, GB, CA),
и полными названиями стран, хранящимися в базе данных (United States, United Kingdom, Canada).
"""

from typing import Optional

# Маппинг кодов стран ISO 3166-1 alpha-2 на полные названия
# Эти названия должны совпадать с тем, как страны хранятся в БД
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

# Обратный маппинг для возможности конвертации названия в код
COUNTRY_NAME_TO_CODE = {v: k for k, v in COUNTRY_CODE_TO_NAME.items()}


def get_country_name_from_code(country_code: str) -> str:
    """
    Конвертирует код страны в полное название.

    Args:
        country_code: Код страны ISO 3166-1 alpha-2 (например, "US", "GB")

    Returns:
        Полное название страны (например, "United States", "United Kingdom")
        Если код не найден в маппинге, возвращает исходный код

    Examples:
        >>> get_country_name_from_code("US")
        "United States"
        >>> get_country_name_from_code("GB")
        "United Kingdom"
        >>> get_country_name_from_code("UNKNOWN")
        "UNKNOWN"
    """
    if not country_code:
        return country_code

    # Нормализуем код к верхнему регистру
    normalized_code = country_code.upper().strip()

    return COUNTRY_CODE_TO_NAME.get(normalized_code, country_code)


def get_country_code_from_name(country_name: str) -> Optional[str]:
    """
    Конвертирует полное название страны в код.

    Args:
        country_name: Полное название страны (например, "United States")

    Returns:
        Код страны ISO 3166-1 alpha-2 (например, "US")
        Если название не найдено в маппинге, возвращает None

    Examples:
        >>> get_country_code_from_name("United States")
        "US"
        >>> get_country_code_from_name("United Kingdom")
        "GB"
        >>> get_country_code_from_name("Unknown Country")
        None
    """
    if not country_name:
        return None

    return COUNTRY_NAME_TO_CODE.get(country_name.strip())


def is_country_code(value: str) -> bool:
    """
    Проверяет, является ли значение кодом страны.

    Args:
        value: Значение для проверки

    Returns:
        True если это код страны, False если это название или неизвестное значение

    Examples:
        >>> is_country_code("US")
        True
        >>> is_country_code("United States")
        False
    """
    if not value or len(value) != 2:
        return False

    return value.upper() in COUNTRY_CODE_TO_NAME
