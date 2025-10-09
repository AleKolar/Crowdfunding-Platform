# src/schemas/webinar.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone


class WebinarBase(BaseModel):
    """Базовая схема вебинара"""
    title: str
    description: str
    scheduled_at: datetime
    duration: int = 60
    max_participants: Optional[int] = 100

    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError('Дата вебинара должна быть в будущем')
        return v

    @field_validator('duration')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Длительность должна быть больше 0')
        if v > 480:
            raise ValueError('Длительность не может превышать 8 часов')
        return v

    @field_validator('max_participants')
    def validate_max_participants(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Количество участников должно быть больше 0')
        return v


class WebinarCreate(WebinarBase):
    """Схема создания вебинара"""
    project_id: int
    creator_id: int


class WebinarUpdate(BaseModel):
    """Схема обновления вебинара"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration: Optional[int] = None
    max_participants: Optional[int] = None
    status: Optional[str] = None
    room_name: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class WebinarResponse(WebinarBase):
    """Схема ответа вебинара"""
    id: int
    project_id: int
    creator_id: int
    room_name: Optional[str] = None
    status: str = "scheduled"
    created_at: datetime
    updated_at: datetime
    available_slots: int = 0
    is_upcoming: bool = True
    is_registered: bool = False

    model_config = ConfigDict(from_attributes=True)


class WebinarListResponse(BaseModel):
    """Схема ответа списка вебинаров"""
    success: bool = True
    webinars: List[WebinarResponse]
    pagination: dict


class WebinarRegistrationBase(BaseModel):
    """Базовая схема регистрации на вебинар"""
    webinar_id: int


class WebinarRegistrationResponse(WebinarRegistrationBase):
    """Схема ответа регистрации"""
    id: int
    user_id: int
    registered_at: datetime
    attended: bool = False
    reminder_sent: bool = False

    model_config = ConfigDict(from_attributes=True)


class WebinarRegistrationSuccessResponse(BaseModel):
    """Схема успешной регистрации на вебинар"""
    success: bool = True
    message: str
    registration_id: int
    webinar_title: str
    scheduled_at: datetime
    already_registered: bool = False


class WebinarJoinResponse(BaseModel):
    """Схема ответа для присоединения к вебинару"""
    success: bool = True
    participant_token: str
    room_name: str
    webinar_title: str


class WebinarAnnouncementResponse(BaseModel):
    """Схема ответа для анонсов вебинаров"""
    success: bool = True
    announcements: List[dict]
    count: int


# Импорт для избежания circular imports
from .project import ProjectResponse

class WebinarWithProjectResponse(WebinarResponse):
    """Вебинар с информацией о проекте"""
    project: Optional[ProjectResponse] = None