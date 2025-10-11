# src/endpoints/auth.py
import logging
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.postgres import get_db
from src.database import models
from src.schemas.auth import LoginResponse, Verify2FARequest, TokenResponse, UserLogin, UserRegister
from src.security.auth import get_current_user, get_user_by_email, generate_and_send_verification_codes
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)

auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)


@auth_router.post("/register", status_code=201)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    return await AuthService.register_user(user_data, db)


@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Первый этап аутентификации - проверка email и секретного кода
    """
    return await AuthService.login_user(login_data, db)


@auth_router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    verify_data: Verify2FARequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Второй этап аутентификации - верификация кода (SMS/Email)
    """
    return await AuthService.verify_2fa(verify_data, db)


@auth_router.post("/resend-code")
async def resend_verification_code(
        request: dict,
        db: AsyncSession = Depends(get_db)
):
    """Повторная отправка кода подтверждения по SMS и Email"""
    email = request.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email обязателен"
        )

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Генерируем и отправляем новые коды по SMS и Email
    result = await generate_and_send_verification_codes(db, user)

    return {
        "message": "Новые коды подтверждения отправлены по SMS и Email",
        "test_sms_code": result["sms_code"],  # Для разработки
        "test_email_code": result["email_code"],  # Для разработки
        "user_phone": user.phone,
        "user_email": user.email
    }


@auth_router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Получение профиля текущего пользователя
    """
    return await AuthService.get_current_user_profile(current_user)


@auth_router.post("/logout")
async def logout():
    """
    Выход из системы (на клиенте удаляется токен)
    """
    return {"message": "Successfully logged out"}


@auth_router.post("/test-email")
async def test_email(to_email: str):
    """
    Тестирование отправки email
    """
    from src.services.email_service import email_service

    success = await email_service.send_welcome_email(to_email, "Test User")

    if success:
        return {"message": "✅ Тестовое письмо отправлено успешно"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="❌ Ошибка отправки тестового письма"
        )