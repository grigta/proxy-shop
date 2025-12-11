"""Bot configuration settings."""
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Bot configuration settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    SUPPORT_USER_ID: int = 8171638354
    
    # Backend API
    BACKEND_API_URL: str
    
    # Redis Storage
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # i18n
    DEFAULT_LOCALE: str = "ru"
    I18N_DOMAIN: str = "messages"
    LOCALES_DIR: str = "bot/locales"
    
    # Pagination
    PROXIES_PER_PAGE: int = 10
    EXPAND_PROXIES_OPTIONS: list[int] = [25, 50, 100]
    
    # Payment
    MIN_DEPOSIT_USD: float = 10.0
    
    # Links
    NEWS_CHANNEL_URL: str = "https://t.me/+cbY_KRGB_hc3MGQ5"
    MIRROR_CHANNEL_URL: str = "https://t.me/+AvjySvNq2KZlMTBi"
    RULES_URL: str = "https://telegra.ph/Usenet-bot-rules-12-04"
    
    # Validation
    PROXY_REFUND_WINDOW_MINUTES: int = 30
    PPTP_REFUND_WINDOW_HOURS: int = 24
    
    @field_validator("TELEGRAM_BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate that bot token contains colon separator."""
        if ":" not in v:
            raise ValueError("TELEGRAM_BOT_TOKEN must contain ':' separator")
        return v
    
    @field_validator("BACKEND_API_URL")
    @classmethod
    def validate_backend_url(cls, v: str) -> str:
        """Validate that backend URL is a proper HTTP(S) URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("BACKEND_API_URL must start with http:// or https://")
        return v.rstrip("/")
    
    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate that Redis URL starts with redis://."""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with redis://")
        return v


# Global settings instance
bot_settings = BotSettings()
