# src/services/auth_service.py
import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from src.database import models
from src.schemas.auth import UserRegister, UserLogin, Verify2FARequest
from src.security.auth import (
    get_user_by_email,
    get_user_by_phone,
    get_password_hash,
    authenticate_user,
    generate_and_send_verification_codes,  # ✅ Используем новый метод
    verify_sms_code,
    create_access_token
)
from src.tasks.tasks import send_welcome_email

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    async def register_user(user_data: UserRegister, db: AsyncSession) -> dict:
        """
        Регистрация нового пользователя
        """
        # Проверка существующего email
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован"
            )

        # Проверка существующего телефона
        existing_user = await get_user_by_phone(db, user_data.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Телефон уже зарегистрирован"
            )

        # Создание пользователя
        hashed_password = get_password_hash(user_data.password)

        new_user = models.User(
            email=user_data.email,
            phone=user_data.phone,
            username=user_data.username,
            secret_code=user_data.secret_code,
            hashed_password=hashed_password,
            is_2fa_enabled=True
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"✅ Пользователь зарегистрирован: {new_user.id}")

        # ✅ ОТПРАВКА ПРИВЕТСТВЕННОГО ПИСЬМА ЧЕРЕЗ CELERY
        send_welcome_email.delay(
            user_email=new_user.email,
            username=new_user.username
        )

        return {
            "message": "Пользователь зарегистрирован успешно. Проверьте вашу почту для приветственного письма.",
            "user_id": new_user.id,
            "email": new_user.email,
            "username": new_user.username
        }

    @staticmethod
    async def login_user(login_data: UserLogin, db: AsyncSession) -> dict:
        """
        Первый этап аутентификации
        """
        user = await authenticate_user(db, login_data.email, login_data.secret_code)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или секретный код",
            )

        # ✅ ОТПРАВЛЯЕМ КОДЫ И ПО SMS И ПО EMAIL
        result = await generate_and_send_verification_codes(db, user)

        return {
            "requires_2fa": True,
            "message": "Коды подтверждения отправлены по SMS и Email",
            "user_id": user.id,  # ✅ ВАЖНО: возвращаем user_id для verify-2fa
            "test_sms_code": result["sms_code"],
            "test_email_code": result["email_code"],
            "user_phone": user.phone,
            "user_email": user.email,
            "note": "Это тестовый режим - используйте любой из кодов выше для входа"
        }

    @staticmethod
    async def verify_2fa(verify_data: Verify2FARequest, db: AsyncSession) -> dict:
        """
        Второй этап аутентификации - верификация кода
        """
        # ✅ ИСПОЛЬЗУЕМ user_id ИЗ ЗАПРОСА (без изменений в схеме)
        result = await db.execute(select(models.User).where(models.User.id == verify_data.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        # Проверяем код
        is_valid = await verify_sms_code(db, user.id, verify_data.sms_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный код подтверждения",
            )

        # Создаем access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "2fa_verified": True,
                "email": user.email
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }

    @staticmethod
    async def get_current_user_profile(current_user: models.User) -> dict:
        """
        Получение профиля текущего пользователя
        """
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "username": current_user.username,
            "is_2fa_enabled": current_user.is_2fa_enabled
        }

    @staticmethod
    async def get_protected_data(current_user: models.User) -> dict:
        """
        Получение защищенных данных пользователя
        """
        return {
            "message": "Доступ к защищенным данным разрешен",
            "user_id": current_user.id,
            "email": current_user.email,
            "data": "Ваши секретные данные здесь"
        }

    @staticmethod
    async def resend_sms_code(user_id: int, db: AsyncSession) -> dict[str, Any]:
        """
        Повторная отправка кодов подтверждения
        """
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        # ✅ ОТПРАВЛЯЕМ КОДЫ И ПО SMS И ПО EMAIL
        result = await generate_and_send_verification_codes(db, user)

        return {
            "message": "Новые коды подтверждения отправлены по SMS и Email",
            "test_sms_code": result["sms_code"],
            "test_email_code": result["email_code"]
        }