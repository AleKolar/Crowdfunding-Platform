# src/config/settings.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # PostgreSQL
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "crowdfunding_db")
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

    # SMS
    SMS_CODE_EXPIRE_MINUTES = int(os.getenv("SMS_CODE_EXPIRE_MINUTES", "10"))
    SMS_API_KEY = os.getenv("SMS_API_KEY", "")
    SMS_API_URL = os.getenv("SMS_API_URL", "")

    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

    # Template settings
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates"
    STATIC_DIR: Path = Path(__file__).parent.parent / "static"

    # Platform settings
    PLATFORM_URL: str = os.getenv("PLATFORM_URL", "https://localhost:8000")

    # LiveKit настройки (опциональные)
    LIVEKIT_HOST = os.getenv("LIVEKIT_HOST", default="http://localhost:7880")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", default="mock_api_key")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", default="mock_api_secret")

    # Флаг для определения, используем ли мы реальный LiveKit
    USE_REAL_LIVEKIT: bool = bool(os.getenv("USE_REAL_LIVEKIT", "False").lower() in {"1", "true", "yes"})

    # Stripe (для платежей)
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Websocket (для оповещений)
    WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT", "8001")




    @property
    def DATABASE_URL(self) -> str:
        """Асинхронный URL для FastAPI с asyncpg"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """URL для синхронных операций (Alembic)"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()