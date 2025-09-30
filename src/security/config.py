import os
from datetime import timedelta
from typing import Optional


class Settings:
    # Безопасная генерация SECRET_KEY
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-insecure-key-for-dev-only")
    ALGORITHM: str = "HS256"

    # JWT настройки
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

    # 2FA настройки
    SMS_CODE_EXPIRE_MINUTES: int = int(os.getenv("SMS_CODE_EXPIRE_MINUTES", "10"))
    MAX_SMS_ATTEMPTS: int = 3

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

    # SMS provider
    SMS_API_KEY: str = os.getenv("SMS_API_KEY", "dev-key")
    SMS_API_URL: str = os.getenv("SMS_API_URL", "https://api.sms-provider.com")

    # Security
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    @classmethod
    def validate_config(cls):
        """Валидация конфигурации при старте"""
        if cls.SECRET_KEY == "fallback-insecure-key-for-dev-only":
            print("⚠️  ВНИМАНИЕ: Используется dev SECRET_KEY! В продакшене установите SECRET_KEY")

        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов")


# Инициализация настроек
settings = Settings()