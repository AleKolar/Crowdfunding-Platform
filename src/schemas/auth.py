# src/schemas/auth.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Схема регистрации пользователя"""
    email: EmailStr
    phone: str
    username: str
    secret_code: str
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

    @validator('phone')
    def phone_format(cls, v):
        # Базовая валидация телефона
        if not v.startswith('+'):
            raise ValueError('Телефон должен начинаться с +')
        return v


class UserLogin(BaseModel):
    """Схема входа пользователя"""
    email: EmailStr
    secret_code: str


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