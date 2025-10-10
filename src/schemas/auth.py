# src/schemas/auth.py
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import re


class UserRegister(BaseModel):
    """Схема регистрации пользователя"""
    email: EmailStr
    phone: str
    username: str
    secret_code: str  # 4 цифры (КОД) пользователя
    password: str

    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Пароль слишком длинный. Максимум 72 байта.')
        return v

    @field_validator('phone')
    def phone_format(cls, v):
        # Убираем все пробелы, дефисы, скобки для проверки
        clean_phone = re.sub(r'[\s\-\(\)]', '', v)

        if len(clean_phone) != 12:
            raise ValueError('Телефон должен содержать ровно 12 символов (включая +)')

        # Разрешаем два формата: +79001234567 или 89001234567
        if not re.match(r'^(\+\d{11}|\d{12})$', clean_phone):
            raise ValueError('Неверный формат телефона. Пример: +79001234567 или 89001234567')

        return v

    @field_validator('secret_code')
    def validate_secret_code(cls, v):
        if not v.isdigit():
            raise ValueError('Секретный код должен содержать только цифры')
        if len(v) != 4:
            raise ValueError('Секретный код должен быть 4 цифры')
        return v


class UserLogin(BaseModel):
    """Схема входа пользователя - ТОЛЬКО email и секретный код"""
    email: EmailStr
    secret_code: str

    @field_validator('secret_code')
    def validate_secret_code(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError('Секретный код должен быть 4 цифры')
        return v


class Verify2FARequest(BaseModel):
    """Схема верификации 2FA"""
    user_id: int
    sms_code: str


class TokenResponse(BaseModel):
    """Схема ответа с токеном"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int


class LoginResponse(BaseModel):
    """Схема ответа после первого этапа логина"""
    requires_2fa: bool = True
    message: str
    user_id: int


class SMSVerificationCodeBase(BaseModel):
    """Базовая схема SMS кода"""
    phone: str
    code: str


class SMSVerificationCodeCreate(SMSVerificationCodeBase):
    """Схема создания SMS кода"""
    user_id: int


class SMSVerificationCodeResponse(SMSVerificationCodeBase):
    """Схема ответа SMS кода"""
    id: int
    user_id: int
    is_used: bool
    attempt_count: int
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True