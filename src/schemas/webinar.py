# src/schemas/webinar.py
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class WebinarBase(BaseModel):
    """Базовая схема вебинара"""
    title: str
    description: str
    scheduled_at: datetime
    duration: int
    max_participants: Optional[int] = None


class WebinarCreate(WebinarBase):
    """Схема создания вебинара"""
    project_id: int

    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Дата вебинара должна быть в будущем')
        return v

    @field_validator('duration')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError('Длительность должна быть больше 0')
        return v


class WebinarUpdate(BaseModel):
    """Схема обновления вебинара"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration: Optional[int] = None
    max_participants: Optional[int] = None
    status: Optional[str] = None


class WebinarResponse(WebinarBase):
    """Схема ответа вебинара"""
    id: int
    project_id: int
    room_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    registered_count: int = 0
    is_registered: bool = False

    class Config:
        from_attributes = True


class WebinarWithProjectResponse(WebinarResponse):
    """Вебинар с информацией о проекте"""
    project: 'ProjectResponse'


class WebinarRegistrationBase(BaseModel):
    """Базовая схема регистрации на вебинар"""
    webinar_id: int


class WebinarRegistrationResponse(WebinarRegistrationBase):
    """Схема ответа регистрации"""
    id: int
    user_id: int
    registered_at: datetime
    attended: bool = False

    class Config:
        from_attributes = True


class WebinarJoinResponse(BaseModel):
    """Схема ответа для присоединения к вебинару"""
    room_id: str
    token: str
    webinar: WebinarResponse

from .project import ProjectResponse

WebinarWithProjectResponse.model_rebuild()