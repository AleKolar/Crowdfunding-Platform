# src/endpoints/auth.py
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from src.database import models
from src.database.postgres import get_db
from src.schemas.auth import UserRegister, LoginResponse, Verify2FARequest, TokenResponse, UserLogin
from src.security.auth import (
    get_user_by_email,
    get_user_by_phone,
    get_password_hash,
    authenticate_user,
    generate_and_send_sms_code,
    verify_sms_code,
    create_access_token,
    get_current_user
)

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))

auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)

# Регистрация
@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Проверяем существование пользователя
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    existing_phone = await get_user_by_phone(db, user_data.phone)
    if existing_phone:
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")

    hashed_password = get_password_hash(user_data.password)

    new_user = models.User(
        email=user_data.email,
        phone=user_data.phone,
        username=user_data.username,
        secret_code=user_data.secret_code,  # Сохраняем как есть (4 цифры)
        hashed_password=hashed_password,
        is_2fa_enabled=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "message": "Пользователь зарегистрирован",
        "user_id": new_user.id,
        "instruction": f"Для входа используйте email и ваш секретный код: {user_data.secret_code}"
    }

# Первый этап аутентификации
@auth_router.post("/login")
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    # Аутентифицируем по email и секретному коду
    user = await authenticate_user(db, login_data.email, login_data.secret_code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или секретный код",
        )

    # Генерируем и отправляем SMS код
    await generate_and_send_sms_code(db, user)

    return LoginResponse(
        requires_2fa=True,
        message="SMS код отправлен на ваш телефон",
        user_id=user.id
    )

# Второй этап - верификация SMS кода
@auth_router.post("/verify-2fa")
async def verify_2fa(
    request: Verify2FARequest,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем SMS код
    is_valid = await verify_sms_code(db, request.user_id, request.sms_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный SMS код",
        )

    # Создаем JWT токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(request.user_id)},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=request.user_id
    )

# Защищенный эндпоинт (теперь тоже асинхронный)
@auth_router.get("/protected-data")
async def protected_data(current_user: models.User = Depends(get_current_user)):
    return {
        "message": "Доступ к защищенным данным разрешен",
        "user_id": current_user.id,
        "email": current_user.email,
        "data": "Ваши секретные данные здесь"
    }

# Повторная отправка SMS кода
@auth_router.post("/resend-sms")
async def resend_sms(user_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await generate_and_send_sms_code(db, user)

    return {"message": "Новый SMS код отправлен"}