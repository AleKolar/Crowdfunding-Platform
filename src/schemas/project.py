# src/schemas/project.py
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    """Базовая схема проекта"""
    title: str
    description: str
    short_description: str
    goal_amount: float
    category: str
    tags: List[str] = []


class ProjectCreate(ProjectBase):
    """Схема создания проекта"""

    @validator('goal_amount')
    def validate_goal_amount(cls, v):
        if v <= 0:
            raise ValueError('Целевая сумма должна быть больше 0')
        return v


class ProjectUpdate(BaseModel):
    """Схема обновления проекта"""
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Схема ответа проекта"""
    id: int
    creator_id: int
    cover_image: Optional[str]
    current_amount: float
    status: str
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    end_date: Optional[datetime]

    # Progress calculation
    @property
    def progress_percentage(self) -> float:
        if self.goal_amount == 0:
            return 0
        return min(100, (self.current_amount / self.goal_amount) * 100)

    @property
    def days_remaining(self) -> Optional[int]:
        if self.end_date:
            delta = self.end_date - datetime.utcnow()
            return max(0, delta.days)
        return None

    class Config:
        from_attributes = True


class ProjectWithCreatorResponse(ProjectResponse):
    """Проект с информацией о создателе"""
    creator: 'UserResponse'


class PostBase(BaseModel):
    """Базовая схема поста"""
    content: str
    post_type: str = "update"
    is_pinned: bool = False


class PostCreate(PostBase):
    """Схема создания поста"""
    project_id: Optional[int] = None
    media_urls: List[str] = []


class PostUpdate(BaseModel):
    """Схема обновления поста"""
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    media_urls: Optional[List[str]] = None


class PostResponse(PostBase):
    """Схема ответа поста"""
    id: int
    author_id: int
    project_id: Optional[int]
    media_urls: List[str]
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    repost_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True


class PostWithAuthorResponse(PostResponse):
    """Пост с информацией об авторе"""
    author: 'UserResponse'


class LikeBase(BaseModel):
    """Базовая схема лайка"""
    post_id: int


class LikeResponse(LikeBase):
    """Схема ответа лайка"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RepostBase(BaseModel):
    """Базовая схема репоста"""
    original_post_id: int


class RepostResponse(RepostBase):
    """Схема ответа репоста"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

from .user import UserResponse

ProjectWithCreatorResponse.update_forward_refs()
PostWithAuthorResponse.update_forward_refs()