# src/security/auth.py
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import secrets

from src.config.settings import settings
from src.database import models
from src.database.postgres import get_db
from src.services.email_service import email_service
from src.services.sms_service import sms_service

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
    bcrypt__rounds=12,
)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "2fa_verified": True,
        "iss": "your-auth-service",
        "aud": "your-api-service"
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
        db: AsyncSession = Depends(get_db)
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

    result = await db.execute(
        select(models.User).where(models.User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


async def authenticate_user(db: AsyncSession, email: str, secret_code: str):
    """Аутентификация пользователя по email и секретному коду"""
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        return False

    # ПРЯМОЕ СРАВНЕНИЕ! Не хэшируем!
    if user.secret_code != secret_code:
        return False

    return user


async def generate_and_send_verification_codes(db: AsyncSession, user: models.User) -> dict:
    """Генерация и отправка кодов подтверждения по SMS и Email"""
    # Генерируем единый код для обоих каналов
    code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.now() + timedelta(minutes=settings.SMS_CODE_EXPIRE_MINUTES)

    # Удаляем старые коды пользователя
    await db.execute(
        delete(models.SMSVerificationCode).where(
            models.SMSVerificationCode.user_id == user.id
        )
    )

    # Сохраняем код в базу
    sms_code = models.SMSVerificationCode(
        user_id=user.id,
        phone=user.phone,
        code=code,
        expires_at=expires_at
    )
    db.add(sms_code)
    await db.commit()
    await db.refresh(sms_code)

    # ✅ ОТПРАВКА SMS
    sms_success = await sms_service.send_verification_code(user.phone, code)

    # ✅ ОТПРАВКА EMAIL
    email_success = await email_service.send_verification_code_email(
        to_email=user.email,
        username=user.username,
        verification_code=code
    )

    # Логируем для разработки
    logger.info(f"🔐 Коды отправлены для {user.email}: SMS={sms_success}, Email={email_success}")
    print(f"📱 SMS код для {user.phone}: {code}")
    print(f"📧 Email код для {user.email}: {code}")

    return {
        "sms_code": code,
        "email_code": code,
        "sms_sent": sms_success,
        "email_sent": email_success
    }


async def verify_sms_code(db: AsyncSession, user_id: int, code: str):
    """Верификация кода подтверждения"""
    now = datetime.now()

    result = await db.execute(
        select(models.SMSVerificationCode).where(
            models.SMSVerificationCode.user_id == user_id,
            models.SMSVerificationCode.code == code,
            models.SMSVerificationCode.is_used == False,
            models.SMSVerificationCode.expires_at >= now
        )
    )
    sms_code = result.scalar_one_or_none()

    if sms_code and sms_code.attempt_count < 3:
        sms_code.attempt_count += 1
        if sms_code.code == code:
            sms_code.is_used = True
            await db.commit()
            return True
        await db.commit()

    return False


async def get_user_by_email(db: AsyncSession, email: str):
    """Получение пользователя по email"""
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str):
    """Получение пользователя по телефону"""
    result = await db.execute(
        select(models.User).where(models.User.phone == phone)
    )
    return result.scalar_one_or_none()


async def cleanup_expired_sms_codes(db: AsyncSession):
    """Очистка просроченных кодов"""
    now = datetime.now()
    result = await db.execute(
        select(models.SMSVerificationCode).where(
            models.SMSVerificationCode.expires_at < now
        )
    )
    expired_codes = result.scalars().all()

    for code in expired_codes:
        await db.delete(code)

    await db.commit()
    return len(expired_codes)