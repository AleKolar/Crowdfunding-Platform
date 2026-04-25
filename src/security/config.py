# src/security/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ✅ JWT НАСТРОЙКИ (из security/config.py)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-insecure-key-for-dev-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

    # ✅ 2FA НАСТРОЙКИ (из security/config.py)
    SMS_CODE_EXPIRE_MINUTES: int = int(os.getenv("SMS_CODE_EXPIRE_MINUTES", "10"))
    MAX_SMS_ATTEMPTS: int = 3

    # ✅ БАЗА ДАННЫХ (из config/settings.py)
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "crowdfunding_db")
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"

    # ✅ REDIS (из config/settings.py)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # ✅ SMS ПРОВАЙДЕР (из security/config.py + config/settings.py)
    SMS_API_KEY: str = os.getenv("SMS_API_KEY", "dev-key")
    SMS_API_URL: str = os.getenv("SMS_API_URL", "https://api.sms-provider.com")

    # ✅ EMAIL (из config/settings.py)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    # ✅ CELERY (из config/settings.py)
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

    # ✅ ШАБЛОНЫ И СТАТИКА (из config/settings.py)
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates"
    STATIC_DIR: Path = Path(__file__).parent.parent / "static"

    # ✅ ПЛАТФОРМА (из config/settings.py)
    PLATFORM_URL: str = os.getenv("PLATFORM_URL", "https://localhost:8000")

    # ✅ LIVEKIT (из config/settings.py)
    LIVEKIT_HOST = os.getenv("LIVEKIT_HOST", "http://localhost:7880")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "mock_api_key")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "mock_api_secret")
    USE_REAL_LIVEKIT: bool = bool(os.getenv("USE_REAL_LIVEKIT", "False").lower() in {"1", "true", "yes"})

    # ✅ STRIPE (из config/settings.py)
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # ✅ WEBSOCKET (из config/settings.py)
    WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT", "8001")

    # ✅ SECURITY (из security/config.py)
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # ✅ СВОЙСТВА ДЛЯ URL (из config/settings.py)
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

    @classmethod
    def validate_config(cls):
        """Валидация конфигурации при старте"""
        print(f"🔧 CONFIG: SECRET_KEY = {cls.SECRET_KEY}")
        print(f"🔧 CONFIG: DATABASE_URL = {cls.DATABASE_URL}")

        if cls.SECRET_KEY == "fallback-insecure-key-for-dev-only":
            print("⚠️  ВНИМАНИЕ: Используется dev SECRET_KEY! В продакшене установите SECRET_KEY")

        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов")

settings = Settings()
settings.validate_config()