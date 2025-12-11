from pydantic_settings import BaseSettings
from pydantic import field_validator, HttpUrl
from typing import Optional
from decimal import Decimal


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DATABASE_ECHO: bool = False
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ============================================
    # HELEKET PAYMENT API CONFIG (ACTIVE)
    # ============================================
    HELEKET_MERCHANT_UUID: str
    HELEKET_API_KEY: str
    HELEKET_WEBHOOK_URL: str
    HELEKET_API_TIMEOUT: int = 30
    MIN_DEPOSIT_USD: Decimal = Decimal('10.00')

    # ============================================
    # LEGACY CRYPTO API CONFIG (DEPRECATED)
    # ============================================
    # DEPRECATED: Legacy cryptocurrencyapi.net config, kept for backward compatibility
    # with /webhook/ipn endpoint. Will be removed in future version.
    CRYPTO_API_KEY: Optional[str] = None
    CRYPTO_API_BASE_URL: str = "https://new.cryptocurrencyapi.net/api"
    CRYPTO_API_IPN_SECRET: Optional[str] = None
    CRYPTO_API_TIMEOUT: int = 30
    IPN_WEBHOOK_URL: Optional[str] = None
    USDT_TRC20_MAIN_WALLET: Optional[str] = None

    # Proxy Configuration
    PROXY_CHECK_TIMEOUT: int = 5
    PROXY_CHECK_URL: str = "https://httpbin.org/ip"
    SOCKS5_DURATION_HOURS: int = 24
    PPTP_DURATION_HOURS: int = 24
    PROXY_EXTEND_PRICE_PERCENTAGE: int = 100

    # External SOCKS API Configuration
    EXTERNAL_SOCKS_API_URL: str = "http://91.142.73.7:8080/api/v1/authorized"
    EXTERNAL_SOCKS_API_TOKEN: str
    EXTERNAL_SOCKS_API_TIMEOUT: int = 30
    EXTERNAL_SOCKS_PRICE: Decimal = Decimal('2.00')
    EXTERNAL_SOCKS_SYNC_INTERVAL_MINUTES: int = 5

    # Telegram Bot Configuration
    TELEGRAM_BOT_USERNAME: str
    WEB_BASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    BACKEND_API_URL: str = "http://localhost:8000"
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("TELEGRAM_BOT_TOKEN")
    def validate_bot_token(cls, v):
        if not v or ":" not in v or len(v) < 40:
            raise ValueError("TELEGRAM_BOT_TOKEN must be a valid bot token from @BotFather (format: 1234567890:ABCdef...)")
        return v

    @field_validator("BACKEND_API_URL")
    def validate_backend_api_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("BACKEND_API_URL must be a valid HTTP/HTTPS URL")
        return v

    @field_validator("REDIS_URL")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a valid redis:// URL")
        return v

    @field_validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")
        return v

    @field_validator("HELEKET_MERCHANT_UUID")
    def validate_heleket_merchant_uuid(cls, v):
        if not v or len(v) < 32:
            raise ValueError("HELEKET_MERCHANT_UUID must be at least 32 characters (UUID format)")
        return v

    @field_validator("HELEKET_API_KEY")
    def validate_heleket_api_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("HELEKET_API_KEY must be at least 32 characters long for security")
        return v

    @field_validator("HELEKET_WEBHOOK_URL")
    def validate_heleket_webhook_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("HELEKET_WEBHOOK_URL must be a valid HTTP/HTTPS URL")
        return v

    # DEPRECATED validators for legacy Crypto API fields
    @field_validator("CRYPTO_API_KEY")
    def validate_crypto_api_key(cls, v):
        if v is not None and len(v) < 16:
            raise ValueError("CRYPTO_API_KEY must be at least 16 characters long for security")
        return v

    @field_validator("CRYPTO_API_BASE_URL")
    def validate_crypto_api_base_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("CRYPTO_API_BASE_URL must be a valid HTTP/HTTPS URL")
        return v

    @field_validator("CRYPTO_API_IPN_SECRET")
    def validate_crypto_api_ipn_secret(cls, v):
        if v is not None and len(v) < 16:
            raise ValueError("CRYPTO_API_IPN_SECRET must be at least 16 characters long for security")
        return v

    @field_validator("IPN_WEBHOOK_URL")
    def validate_ipn_webhook_url(cls, v):
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("IPN_WEBHOOK_URL must be a valid HTTP/HTTPS URL")
        return v

    @field_validator("USDT_TRC20_MAIN_WALLET")
    def validate_usdt_trc20_wallet(cls, v):
        if v is not None and (not v.startswith("T") or len(v) != 34):
            raise ValueError("USDT_TRC20_MAIN_WALLET must be a valid TRC-20 address (starts with 'T' and 34 characters long)")
        return v

    @field_validator("PROXY_CHECK_TIMEOUT")
    def validate_proxy_timeout(cls, v):
        if v <= 0 or v > 30:
            raise ValueError("PROXY_CHECK_TIMEOUT must be between 1 and 30 seconds")
        return v

    @field_validator("PROXY_CHECK_URL")
    def validate_proxy_check_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("PROXY_CHECK_URL must be a valid HTTP/HTTPS URL")
        return v

    @field_validator("TELEGRAM_BOT_USERNAME")
    def validate_bot_username(cls, v):
        if not v or "@" in v:
            raise ValueError("TELEGRAM_BOT_USERNAME must be a valid bot username without @ symbol")
        return v

    @field_validator("WEB_BASE_URL")
    def validate_web_base_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("WEB_BASE_URL must be a valid HTTP/HTTPS URL")
        return v

    @field_validator("EXTERNAL_SOCKS_API_TOKEN")
    def validate_external_socks_token(cls, v):
        if not v or len(v) < 8:
            raise ValueError("EXTERNAL_SOCKS_API_TOKEN must be at least 8 characters long")
        return v

    @field_validator("EXTERNAL_SOCKS_API_URL")
    def validate_external_socks_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("EXTERNAL_SOCKS_API_URL must be a valid HTTP/HTTPS URL")
        return v

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()