# src/schemas/webinar.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# Базовые схемы
class WebinarBase(BaseModel):
    title: str
    description: str
    scheduled_at: datetime
    duration: int = 60
    max_participants: int = 100
    is_public: bool = True


# Создание вебинара
class WebinarCreate(WebinarBase):
    meta_data: Optional[Dict[str, Any]] = None


# Обновление вебинара
class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration: Optional[int] = None
    max_participants: Optional[int] = None
    is_public: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


# Ответ с вебинаром
class Webinar(WebinarBase):
    id: int
    creator_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Старые схемы для обратной совместимости
class WebinarResponse(Webinar):
    project_id: Optional[int] = None
    room_name: Optional[str] = None
    available_slots: Optional[int] = None
    is_upcoming: Optional[bool] = None
    is_registered: Optional[bool] = None

    # Убираем computed_field, так как данные теперь приходят из репозитория


class WebinarListResponse(BaseModel):
    webinars: List[WebinarResponse]
    pagination: Dict[str, Any]


class WebinarRegistrationSuccessResponse(BaseModel):
    success: bool
    message: str
    webinar_id: int
    webinar_title: str


class WebinarJoinResponse(BaseModel):
    success: bool
    join_url: Optional[str] = None
    token: Optional[str] = None
    message: str


class WebinarAnnouncementResponse(BaseModel):
    announcements: List[Dict[str, Any]]
    count: int


class UserWebinarsResponse(BaseModel):
    success: bool
    webinars: List[Dict[str, Any]]
    pagination: Dict[str, Any]