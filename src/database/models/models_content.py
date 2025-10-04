# src/database/models/models_content.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    GIF = "gif"
    OTHER = "other"


class ProjectStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class PostType(enum.Enum):
    UPDATE = "update"
    MILESTONE = "milestone"
    NEWS = "news"
    VIDEO = "video"
    AUDIO = "audio"
    ANNOUNCEMENT = "announcement"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    short_description = Column(String(500))
    cover_image = Column(String)  # Главное изображение проекта
    goal_amount = Column(Float)
    current_amount = Column(Float, default=0.0)
    category = Column(String)
    tags = Column(JSON)  # Список тегов
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    end_date = Column(DateTime)
    is_featured = Column(Boolean, default=False)

    # Новые поля для видео и медиа
    video_url = Column(String, nullable=True)  # Главное видео проекта
    video_thumbnail = Column(String, nullable=True)  # Превью видео
    video_duration = Column(Integer, nullable=True)  # Длительность в секундах

    # Аудио поддержка
    audio_url = Column(String, nullable=True)  # Главное аудио проекта
    audio_duration = Column(Integer, nullable=True)  # Длительность аудио в секундах

    # Дополнительные поля
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    backers_count = Column(Integer, default=0)  # Количество поддержавших

    # НОВЫЕ ПОЛЯ ДЛЯ СТАТИСТИКИ ДОНАТОВ
    total_donations = Column(Float, default=0.0)  # Общая сумма донатов
    last_donation_at = Column(DateTime, nullable=True)  # Дата последнего доната

    # Связи
    creator = relationship("User", back_populates="projects")
    posts = relationship("Post", back_populates="project", cascade="all, delete-orphan")
    webinars = relationship("Webinar", back_populates="project", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="project", cascade="all, delete-orphan")
    media = relationship("ProjectMedia", back_populates="project", cascade="all, delete-orphan")
    updates = relationship("ProjectUpdate", back_populates="project", cascade="all, delete-orphan")

    # Computed properties
    @property
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return min(100, round((self.current_amount / self.goal_amount) * 100, 2))

    @property
    def days_remaining(self):
        if self.end_date:
            delta = self.end_date - datetime.now()
            return max(0, delta.days)
        return None

    @property
    def is_funded(self):
        return self.current_amount >= self.goal_amount


class ProjectMedia(Base):
    __tablename__ = "project_media"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    file_url = Column(String)
    file_type = Column(Enum(MediaType))
    file_name = Column(String)
    file_size = Column(Integer)  # в байтах
    duration = Column(Integer, nullable=True)  # для видео/аудио в секундах
    thumbnail_url = Column(String, nullable=True)  # превью для видео/аудио
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)  # порядок отображения
    is_approved = Column(Boolean, default=True)
    mime_type = Column(String, nullable=True)  # MIME тип файла
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", back_populates="media")


class ProjectUpdate(Base):
    __tablename__ = "project_updates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String)
    content = Column(Text)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", back_populates="updates")
    media = relationship("UpdateMedia", back_populates="project_update", cascade="all, delete-orphan")


class UpdateMedia(Base):
    __tablename__ = "update_media"

    id = Column(Integer, primary_key=True, index=True)
    update_id = Column(Integer, ForeignKey("project_updates.id"))
    file_url = Column(String)
    file_type = Column(Enum(MediaType))
    file_name = Column(String)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    project_update = relationship("ProjectUpdate", back_populates="media")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    post_type = Column(Enum(PostType), default=PostType.UPDATE)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Медиа поля
    media_url = Column(String, nullable=True)  # Основное медиа поста
    media_thumbnail = Column(String, nullable=True)  # Превью медиа
    media_duration = Column(Integer, nullable=True)  # Длительность для видео/аудио

    # Статистика
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)

    author = relationship("User")
    project = relationship("Project", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    reposts = relationship("Repost", back_populates="original_post", cascade="all, delete-orphan")
    media = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class PostMedia(Base):
    __tablename__ = "post_media"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    file_url = Column(String)
    file_type = Column(Enum(MediaType))
    file_name = Column(String)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("Post", back_populates="media")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # Для вложенных комментариев
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    post = relationship("Post", back_populates="comments")
    user = relationship("User")
    parent = relationship("Comment", remote_side=[id], backref="replies")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")
    post = relationship("Post", back_populates="likes")


class Repost(Base):
    __tablename__ = "reposts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")
    original_post = relationship("Post", back_populates="reposts")