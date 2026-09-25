"""
Core Configuration module using Pydantic Settings.
Manages all environment parameters, risk thresholds, exchange credentials, and notification secrets.
"""

import os
from typing import Any

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings, Field  # type: ignore[no-redef]
    except ImportError:

        def Field(default: Any = None, **kwargs: Any) -> Any:  # type: ignore[misc]
            return default

        class BaseSettings:  # type: ignore[no-redef]
            def __init__(self, **kwargs: Any):
                for k, v in self.__class__.__dict__.items():
                    if not k.startswith("_") and not callable(v):
                        env_val = os.getenv(k)
                        if env_val is not None:
                            val_type = type(v) if v is not None else str
                            try:
                                if val_type is bool:
                                    setattr(
                                        self, k, env_val.lower() in ("1", "true", "yes")
                                    )
                                elif val_type in (int, float):
                                    setattr(self, k, val_type(env_val))
                                else:
                                    setattr(self, k, env_val)
                            except Exception:
                                setattr(self, k, env_val)
                        else:
                            setattr(self, k, v)
                for k, v in kwargs.items():
                    setattr(self, k, v)


class Settings(BaseSettings):
    # Application Metadata
    APP_NAME: str = "MONEY For HONEY"
    TAGLINE: str = (
        "autonomous Trading system and build self wealth engine for the future"
    )
    APP_ENV: str = "production"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security & Encryption
    SECRET_KEY: str = "honey_production_secret_key_change_me"
    FERNET_KEY: str | None = (
        None  # Base64 32-byte key for encrypting exchange credentials
    )
    TESTNET_MODE: bool = Field(
        default=True, description="Enables sandbox/testnet mode for safety"
    )
    STRICT_PRODUCTION_MODE: bool = Field(
        default=False,
        description="Disallows simulated fallbacks if API keys are missing/invalid in production",
    )
    TELEGRAM_WEBHOOK_SECRET: str = Field(
        default="honey_telegram_secret_token_change_me",
        description="Secret token for verifying Telegram Webhook requests",
    )

    # Exchange API Credentials
    BINANCE_API_KEY: str | None = None
    BINANCE_API_SECRET: str | None = None
    BYBIT_API_KEY: str | None = None
    BYBIT_API_SECRET: str | None = None
    OKX_API_KEY: str | None = None
    OKX_API_SECRET: str | None = None
    OKX_PASSPHRASE: str | None = None

    # Quantitative Risk Parameters
    RISK_PER_TRADE_PCT: float = Field(
        default=0.015, description="1.5% maximum risk per trade"
    )
    DAILY_DRAWDOWN_CAP_PCT: float = Field(
        default=0.05, description="5.0% daily circuit breaker limit"
    )
    MAX_EQUITY_ALLOCATION_PCT: float = Field(
        default=0.30, description="Max 30% total equity per position"
    )
    MIN_BINANCE_ORDER_USDT: float = Field(
        default=10.0, description="Binance spot minimum order notional"
    )
    SLIPPAGE_TOLERANCE_PCT: float = Field(
        default=0.0005, description="0.05% max allowed slippage"
    )

    # Vault & Compounding Parameters
    MAINTENANCE_FEE_PCT: float = Field(
        default=0.05, description="5% platform maintenance fee on gross profit"
    )
    REINVEST_PCT: float = Field(
        default=0.70, description="70% net profit reinvested into active trading"
    )
    VAULT_RESERVE_PCT: float = Field(
        default=0.30, description="30% net profit channeled to earn vault"
    )
    VAULT_LOCKED_THRESHOLD: float = Field(
        default=100.0, description="Threshold in USDT to trigger locked staking"
    )

    # Spatial Arbitrage Engine Parameters
    MIN_ARBITRAGE_SPREAD_PCT: float = Field(
        default=0.006, description="0.6% minimum net profit spread"
    )
    ARBITRAGE_SYMBOLS: list[str] = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "XRP/USDT",
        "AVAX/USDT",
    ]

    # Notifications
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    TELEGRAM_CHANNEL_ID: str | None = None
    WHATSAPP_API_URL: str | None = None
    WHATSAPP_PHONE_NUMBER: str | None = None
    WHATSAPP_API_TOKEN: str | None = None

    # Databases
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = (
        "postgresql://honey_admin:honey_secret_pass@localhost:5432/money_for_honey"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
