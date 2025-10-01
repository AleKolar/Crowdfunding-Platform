# src/schemas/project.py
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .user import UserResponse


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    GIF = "gif"
    OTHER = "other"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class PostType(str, Enum):
    UPDATE = "update"
    MILESTONE = "milestone"
    NEWS = "news"
    VIDEO = "video"
    AUDIO = "audio"
    ANNOUNCEMENT = "announcement"


# Схемы для медиа
class ProjectMediaBase(BaseModel):
    file_url: str
    file_type: MediaType
    file_name: str
    description: Optional[str] = None
    sort_order: int = 0


class ProjectMediaCreate(ProjectMediaBase):
    project_id: int


class ProjectMediaUpdate(BaseModel):
    description: Optional[str] = None
    sort_order: Optional[int] = None
    file_name: Optional[str] = None
    is_approved: Optional[bool] = None


class ProjectMediaResponse(ProjectMediaBase):
    id: int
    project_id: int
    file_size: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для проектов
class ProjectBase(BaseModel):
    title: str
    description: str
    short_description: str
    goal_amount: float
    category: str
    tags: List[str] = []


class ProjectCreate(ProjectBase):
    video_url: Optional[str] = None
    video_thumbnail: Optional[str] = None
    video_duration: Optional[int] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None

    @field_validator('goal_amount')
    def validate_goal_amount(cls, v):
        if v <= 0:
            raise ValueError('Целевая сумма должна быть больше 0')
        return v


class ProjectUpdate(BaseModel):  # ← ОБНОВЛЕНИЕ ДАННЫХ ПРОЕКТА
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    cover_image: Optional[str] = None
    video_url: Optional[str] = None
    video_thumbnail: Optional[str] = None
    video_duration: Optional[int] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None
    is_featured: Optional[bool] = None
    goal_amount: Optional[float] = None
    end_date: Optional[datetime] = None

    @field_validator('goal_amount')
    def validate_goal_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Целевая сумма должна быть больше 0')
        return v


class ProjectResponse(ProjectBase):
    id: int
    creator_id: int
    cover_image: Optional[str] = None
    video_url: Optional[str] = None
    video_thumbnail: Optional[str] = None
    video_duration: Optional[int] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None
    current_amount: float
    status: ProjectStatus
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    end_date: Optional[datetime] = None
    views_count: int
    likes_count: int
    shares_count: int
    backers_count: int

    # Computed properties
    progress_percentage: float
    days_remaining: Optional[int]
    is_funded: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectWithMediaResponse(ProjectResponse):
    media: List[ProjectMediaResponse] = []


class ProjectWithCreatorResponse(ProjectResponse):
    creator: UserResponse


# Схемы для постов
class PostBase(BaseModel):
    content: str
    post_type: PostType = PostType.UPDATE
    is_pinned: bool = False


class PostCreate(PostBase):
    project_id: Optional[int] = None
    media_url: Optional[str] = None
    media_thumbnail: Optional[str] = None
    media_duration: Optional[int] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    post_type: Optional[PostType] = None
    is_pinned: Optional[bool] = None
    media_url: Optional[str] = None
    media_thumbnail: Optional[str] = None
    media_duration: Optional[int] = None


class PostResponse(PostBase):
    id: int
    author_id: int
    project_id: Optional[int] = None
    media_url: Optional[str] = None
    media_thumbnail: Optional[str] = None
    media_duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    views_count: int
    likes_count: int
    comments_count: int
    shares_count: int
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


class PostWithAuthorResponse(PostResponse):
    author: UserResponse


class PostWithMediaResponse(PostResponse):
    media: List['PostMediaResponse'] = []


# Схемы для медиа постов
class PostMediaBase(BaseModel):
    file_url: str
    file_type: MediaType
    file_name: str
    sort_order: int = 0


class PostMediaCreate(PostMediaBase):
    post_id: int


class PostMediaUpdate(BaseModel):
    file_url: Optional[str] = None
    file_type: Optional[MediaType] = None
    file_name: Optional[str] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None


class PostMediaResponse(PostMediaBase):
    id: int
    post_id: int
    file_size: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для комментариев
class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    post_id: int


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    parent_id: Optional[int] = None


class CommentResponse(CommentBase):
    id: int
    post_id: int
    user_id: int
    is_edited: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentWithUserResponse(CommentResponse):
    user: UserResponse


# Схемы для лайков и репостов
class LikeResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepostResponse(BaseModel):
    id: int
    user_id: int
    original_post_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Схемы для ОБНОВЛЕНИЙ ПРОЕКТА (НОВОСТЕЙ) !
class ProjectNewsBase(BaseModel):  #
    title: str
    content: str
    is_public: bool = True

class ProjectNewsCreate(ProjectNewsBase):  #
    project_id: int

class ProjectNewsUpdate(BaseModel):  #
    title: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None

class ProjectNewsResponse(ProjectNewsBase):  #
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    media: List['NewsMediaResponse'] = []  #

    model_config = ConfigDict(from_attributes=True)

# Схемы для медиа обновлений - ПЕРЕИМЕНОВАНО!
class NewsMediaBase(BaseModel):  #
    file_url: str
    file_type: MediaType
    file_name: str

class NewsMediaCreate(NewsMediaBase):  #
    update_id: int  # Осторожно! Это ссылается на project_updates.id

class NewsMediaUpdate(BaseModel):  #
    file_url: Optional[str] = None
    file_type: Optional[MediaType] = None
    file_name: Optional[str] = None

class NewsMediaResponse(NewsMediaBase):  #
    id: int
    update_id: int
    file_size: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Обновляем forward refs
ProjectWithCreatorResponse.model_rebuild()
PostWithAuthorResponse.model_rebuild()
PostWithMediaResponse.model_rebuild()
CommentWithUserResponse.model_rebuild()
ProjectNewsResponse.model_rebuild()  # ← ОБНОВЛЕНО