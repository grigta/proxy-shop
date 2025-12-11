"""i18n middleware for bot localization."""
from typing import Dict, Any, Optional
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiogram.types import User as TelegramUser

from bot.core.config import bot_settings


# Initialize i18n
i18n = I18n(
    path=bot_settings.LOCALES_DIR,
    default_locale=bot_settings.DEFAULT_LOCALE,
    domain=bot_settings.I18N_DOMAIN
)


class CustomI18nMiddleware(SimpleI18nMiddleware):
    """Custom i18n middleware that uses user profile language preference."""
    
    def __init__(self, i18n_instance: I18n):
        """Initialize custom i18n middleware.
        
        Args:
            i18n_instance: I18n instance
        """
        super().__init__(i18n_instance)
    
    async def get_locale(self, event: Any, data: Dict[str, Any]) -> str:
        """Get locale for current user.
        
        Priority:
        1. User profile language from backend
        2. Telegram user language_code
        3. Default locale from settings
        
        Args:
            event: Incoming event
            data: Handler data
            
        Returns:
            Locale code (ru/en)
        """
        # Try to get language from user profile (set by AuthMiddleware)
        user_profile: Optional[Dict[str, Any]] = data.get("user_profile")
        if user_profile and "language" in user_profile:
            lang = user_profile["language"]
            if lang in ["ru", "en"]:
                return lang
        
        # Try to get language from Telegram user
        telegram_user: Optional[TelegramUser] = data.get("event_from_user")
        if telegram_user and telegram_user.language_code:
            lang = telegram_user.language_code
            # Map to supported locales
            if lang.startswith("ru"):
                return "ru"
            elif lang.startswith("en"):
                return "en"
        
        # Return default locale
        return bot_settings.DEFAULT_LOCALE


def setup_i18n_middleware() -> CustomI18nMiddleware:
    """Setup and return i18n middleware instance.
    
    Returns:
        CustomI18nMiddleware instance
    """
    return CustomI18nMiddleware(i18n)


# Export gettext for use in other modules
_ = i18n.gettext
