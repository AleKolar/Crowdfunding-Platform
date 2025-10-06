# src/database/models/auth_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    secret_code = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    # Связи с другими таблицами
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    notification_settings = relationship("UserNotificationSettings", back_populates="user", uselist=False)
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    sms_codes = relationship("SMSVerificationCode", back_populates="user")
    projects = relationship("Project", back_populates="creator")
    donations = relationship("Donation", back_populates="donor")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    reposts = relationship("Repost", back_populates="user")

    # Явные связи для подписок
    subscriptions_as_subscriber = relationship(
        "Subscription",
        primaryjoin="User.id == Subscription.subscriber_id",
        back_populates="subscriber"
    )

    subscriptions_as_creator = relationship(
        "Subscription",
        primaryjoin="User.id == Subscription.creator_id",
        back_populates="creator"
    )


class SMSVerificationCode(Base):
    __tablename__ = "sms_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    phone = Column(String)
    code = Column(String(6))
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)

    user = relationship("User", back_populates="sms_codes")