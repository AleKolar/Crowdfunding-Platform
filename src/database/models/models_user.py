# src/database/models/user_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="profile")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    webinar_reminders = Column(Boolean, default=True)
    new_post_notifications = Column(Boolean, default=True)
    donation_notifications = Column(Boolean, default=True)
    language = Column(String, default="ru")
    currency = Column(String, default="RUB")

    user = relationship("User", back_populates="settings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("users.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

    # IDE "ругается" ,ТО ЖЕ, на foreign_keys, но работает
    subscriber = relationship(
        "User",
        foreign_keys=[subscriber_id],
        back_populates="subscriptions_as_subscriber"
    )

    creator = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="subscriptions_as_creator"
    )

    # IDE "ругается" на типы в foreign_keys, но , вроде, работает
    # subscriber = relationship("User", foreign_keys=[subscriber_id], back_populates="subscriptions_made")
    # creator = relationship("User", foreign_keys=[creator_id], back_populates="subscribers")
    # IDE "ругается" на типы в foreign_keys
    # subscriber = relationship("User", foreign_keys=[subscriber_id], backref="subscriptions_made")
    # creator = relationship("User", foreign_keys=[creator_id], backref="subscribers")