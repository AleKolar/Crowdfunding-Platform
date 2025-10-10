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
from src.services.sms_service import sms_service

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    logger.debug(f"Verifying password for user")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    logger.info(f"Starting password hash process")
    logger.debug(f"Password length: {len(password)} characters")
    logger.debug(f"Password bytes length: {len(password.encode('utf-8'))} bytes")

    try:
        # Проверяем длину в байтах
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            logger.warning(f"Password too long: {len(password_bytes)} bytes, truncating to 72 bytes")
            password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
            logger.debug(f"Truncated password length: {len(password)} characters")

        logger.debug("Calling pwd_context.hash()")
        result = pwd_context.hash(password)
        logger.info("Password hash created successfully")
        return result

    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        logger.exception("Full exception details:")  # Автоматически добавляет traceback
        raise


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


# !!! Этот метод оставляем синхронным для зависимостей FastAPI !!!
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

    # Асинхронный запрос к БД
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


async def generate_and_send_sms_code(db: AsyncSession, user: models.User) -> str:
    """Генерация и отправка SMS кода"""
    code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.now() + timedelta(minutes=settings.SMS_CODE_EXPIRE_MINUTES)

    # Удаляем старые коды пользователя
    await db.execute(
        delete(models.SMSVerificationCode).where(
            models.SMSVerificationCode.user_id == user.id
        )
    )

    sms_code = models.SMSVerificationCode(
        user_id=user.id,
        phone=user.phone,
        code=code,
        expires_at=expires_at
    )
    db.add(sms_code)
    await db.commit()
    await db.refresh(sms_code)

    # В development просто логируем
    print(f"📱 SMS код для {user.phone}: {code}")
    # В production: await sms_service.send_verification_code(user.phone, code)

    return code


async def verify_sms_code(db: AsyncSession, user_id: int, code: str):
    """Верификация SMS кода"""
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
    """Очистка просроченных SMS кодов"""
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