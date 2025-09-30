# src/database/models/content_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    short_description = Column(String(500))
    cover_image = Column(String)
    goal_amount = Column(Float)
    current_amount = Column(Float, default=0.0)
    category = Column(String)
    tags = Column(JSON)  # Список тегов
    status = Column(String, default="draft")  # draft, active, completed, cancelled
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    end_date = Column(DateTime)
    is_featured = Column(Boolean, default=False)

    creator = relationship("User", back_populates="projects")
    posts = relationship("Post", back_populates="project")
    webinars = relationship("Webinar", back_populates="project")
    donations = relationship("Donation", back_populates="project")

    donations = relationship("Donation", back_populates="project")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    media_urls = Column(JSON)  # Список URL изображений/видео
    author_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    post_type = Column(String, default="update")  # update, milestone, news
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User")
    project = relationship("Project", back_populates="posts")
    likes = relationship("Like", back_populates="post")
    reposts = relationship("Repost", back_populates="original_post")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    post = relationship("Post", back_populates="likes")


class Repost(Base):
    __tablename__ = "reposts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    original_post = relationship("Post", back_populates="reposts")