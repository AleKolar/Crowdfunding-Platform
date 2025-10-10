# src/endpoints/auth.py
import logging
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.postgres import get_db
from src.database import models
from src.schemas.auth import LoginResponse, Verify2FARequest, TokenResponse, UserLogin, UserRegister
from src.security.auth import get_current_user
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
    Второй этап аутентификации - верификация SMS кода
    """
    return await AuthService.verify_2fa(verify_data, db)


@auth_router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Получение профиля текущего пользователя
    """
    return await AuthService.get_current_user_profile(current_user)


@auth_router.get("/protected-data")
async def protected_data(current_user: models.User = Depends(get_current_user)):
    """
    Получение защищенных данных (требует аутентификации с подтвержденной 2FA)
    """
    return await AuthService.get_protected_data(current_user)


@auth_router.post("/resend-sms")
async def resend_sms(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Повторная отправка SMS кода
    """
    return await AuthService.resend_sms_code(user_id, db)


@auth_router.post("/logout")
async def logout():
    """
    Выход из системы (на клиенте удаляется токен)
    """
    return {"message": "Successfully logged out"}