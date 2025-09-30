# src/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    phone: str
    username: str
    is_active: bool


class UserCreate(UserBase):
    """Схема создания пользователя"""
    secret_code: str
    password: str


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    phone: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Схема ответа пользователя"""
    id: int
    is_2fa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Базовая схема профиля пользователя"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    """Схема создания профиля"""
    user_id: int


class UserProfileUpdate(UserProfileBase):
    """Схема обновления профиля"""
    avatar_url: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    """Схема ответа профиля"""
    id: int
    user_id: int
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSettingsBase(BaseModel):
    """Базовая схема настроек пользователя"""
    email_notifications: bool = True
    push_notifications: bool = True
    webinar_reminders: bool = True
    new_post_notifications: bool = True
    donation_notifications: bool = True
    language: str = "ru"
    currency: str = "RUB"


class UserSettingsUpdate(UserSettingsBase):
    """Схема обновления настроек"""
    pass


class UserSettingsResponse(UserSettingsBase):
    """Схема ответа настроек"""
    id: int
    user_id: int

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    """Базовая схема подписки"""
    creator_id: int


class SubscriptionCreate(SubscriptionBase):
    """Схема создания подписки"""
    subscriber_id: int


class SubscriptionResponse(SubscriptionBase):
    """Схема ответа подписки"""
    id: int
    subscriber_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithProfileResponse(UserResponse):
    """Расширенная схема пользователя с профилем"""
    profile: Optional[UserProfileResponse] = None
    settings: Optional[UserSettingsResponse] = None