from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)  # Для SMS
    secret_code = Column(String)  # Статический секретный код пользователя
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=True)  # Всегда включена в нашей схеме


class SMSVerificationCode(Base):
    __tablename__ = "sms_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    phone = Column(String)
    code = Column(String(6))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)