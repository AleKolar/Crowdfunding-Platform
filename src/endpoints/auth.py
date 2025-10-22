# src/endpoints/auth.py
import logging
from fastapi import Depends, APIRouter, HTTPException
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.postgres import get_db
from src.database import models
from src.schemas.auth import LoginResponse, Verify2FARequest, TokenResponse, UserLogin, UserRegister
from src.security.auth import get_current_user, get_user_by_email, generate_and_send_verification_codes, oauth2_scheme
from src.security.config import settings
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
    logger.info(f"🔐 LOGIN ATTEMPT: email={login_data.email}")
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

    # ✅ Для совместимости с фронтендом возвращаем оба ключа
    verification_code = result["code"]

    return {
        "message": "Новые коды подтверждения отправлены по SMS и Email",
        "test_sms_code": verification_code,
        "test_email_code": verification_code,
        "sms_sent": result["sms_sent"],
        "email_sent": result["email_sent"],
        "user_phone": user.phone,
        "user_email": user.email
    }

@auth_router.get("/me")
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Получение профиля текущего пользователя
    """
    return await AuthService.get_current_user_profile(current_user)

@auth_router.get("/debug-token")
async def debug_token(token: str = Depends(oauth2_scheme)):
    """Отладочный эндпоинт для проверки токена"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return {
            "user_id": payload.get("sub"),
            "2fa_verified": payload.get("2fa_verified"),
            "email": payload.get("email"),
            "all_payload": payload
        }
    except JWTError as e:
        return {"error": str(e)}


@auth_router.get("/debug-imports")
async def debug_imports():
    """Проверка откуда загружаются настройки"""
    try:
        from src.security.config import settings

        debug_info = {
            "config_loaded": True,
            "config_file": "src.security.config",
            "secret_key_length": len(settings.SECRET_KEY) if hasattr(settings, 'SECRET_KEY') else 0,
            "secret_key_preview": settings.SECRET_KEY[:10] + "..." if hasattr(settings,
                                                                              'SECRET_KEY') else "NO_SECRET_KEY",
        }

        return debug_info

    except Exception as e:
        return {
            "config_loaded": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@auth_router.get("/debug-sms-codes")
async def debug_sms_codes(db: AsyncSession = Depends(get_db)):
    """Просмотр всех SMS кодов в базе (для отладки)"""
    from sqlalchemy import select
    result = await db.execute(select(models.SMSVerificationCode))
    codes = result.scalars().all()

    return {
        "sms_codes": [
            {
                "id": code.id,
                "user_id": code.user_id,
                "phone": code.phone,
                "code": code.code,
                "is_used": code.is_used,
                "attempt_count": code.attempt_count,
                "expires_at": code.expires_at.isoformat() if code.expires_at else None
            }
            for code in codes
        ]
    }

@auth_router.get("/debug-secret")
async def debug_secret():
    """Проверка SECRET_KEY"""
    return {
        "secret_key_from_settings": settings.SECRET_KEY,
        "secret_key_length": len(settings.SECRET_KEY),
        "algorithm": settings.ALGORITHM,
        "expected_secret": "i5GSOGVbEN7l-UJRAoS2Uxjw0s8YU3oKdWMeQGCaw1M",
        "match": settings.SECRET_KEY == "i5GSOGVbEN7l-UJRAoS2Uxjw0s8YU3oKdWMeQGCaw1M"
    }

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