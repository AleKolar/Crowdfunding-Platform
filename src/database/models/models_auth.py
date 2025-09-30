# src/database/models/auth_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)  # Добавим username
    secret_code = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Связи с другими таблицами
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    notification_settings = relationship("UserNotificationSettings", back_populates="user", uselist=False)
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    sms_codes = relationship("SMSVerificationCode", back_populates="user")
    projects = relationship("Project", back_populates="creator")
    donations = relationship("Donation", back_populates="donor")


class SMSVerificationCode(Base):
    __tablename__ = "sms_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    phone = Column(String)
    code = Column(String(6))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)

    user = relationship("User", back_populates="sms_codes")