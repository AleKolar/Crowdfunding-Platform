from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
import secrets

from src.config.settings import settings
from src.database import models
from src.database.postgres import get_db
from src.services.sms_service import sms_service

# Используем настройки из config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "2fa_verified": True,
        "iss": "your-auth-service",  # Issuer
        "aud": "your-api-service"  # Audience
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience="your-api-service"
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="verify-2fa")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """Получение текущего пользователя с проверкой 2FA статуса"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        is_2fa_verified: bool = payload.get("2fa_verified", False)

        if user_id is None or not is_2fa_verified:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # ✅ SQLAlchemy 2.x стиль
    user = db.scalar(
        select(models.User).where(models.User.id == int(user_id))
    )
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(db: Session, email: str, secret_code: str):
    """Аутентификация пользователя по email и секретному коду"""
    # ✅ SQLAlchemy 2.x стиль
    user = db.scalar(
        select(models.User).where(models.User.email == email)
    )
    if not user:
        return False
    if not verify_password(secret_code, user.secret_code):
        return False
    return user


async def generate_and_send_sms_code(db: AsyncSession, user: models.User) -> str:
    """Генерация и отправка SMS кода"""
    code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.now() + timedelta(minutes=settings.SMS_CODE_EXPIRE_MINUTES)

    sms_code = models.SMSVerificationCode(
        user_id=user.id,
        phone=user.phone,
        code=code,
        expires_at=expires_at
    )
    db.add(sms_code)
    await db.commit()
    await db.refresh(sms_code)

    await sms_service.send_verification_code(user.phone, code)
    return code


def verify_sms_code(db: Session, user_id: int, code: str):
    """Верификация SMS кода"""
    # ✅ SQLAlchemy 2.x стиль
    now = datetime.now()

    sms_code = db.scalar(
        select(models.SMSVerificationCode).where(
            models.SMSVerificationCode.user_id == user_id,
            models.SMSVerificationCode.code == code,
            models.SMSVerificationCode.is_used == False,
            models.SMSVerificationCode.expires_at >= now
        )
    )

    if sms_code and sms_code.attempt_count < 3:
        sms_code.attempt_count += 1
        if sms_code.code == code:
            sms_code.is_used = True
            db.commit()
            return True
        db.commit()

    return False


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Получение пользователя по email"""
    # ✅ SQLAlchemy 2.x стиль
    return db.scalar(
        select(models.User).where(models.User.email == email)
    )


def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    """Получение пользователя по телефону"""
    # ✅ SQLAlchemy 2.x стиль
    return db.scalar(
        select(models.User).where(models.User.phone == phone)
    )


def cleanup_expired_sms_codes(db: Session):
    """Очистка просроченных SMS кодов"""
    # ✅ SQLAlchemy 2.x стиль
    now = datetime.now()
    expired_codes = db.scalars(
        select(models.SMSVerificationCode).where(
            models.SMSVerificationCode.expires_at < now
        )
    ).all()

    for code in expired_codes:
        db.delete(code)

    db.commit()
    return len(expired_codes)