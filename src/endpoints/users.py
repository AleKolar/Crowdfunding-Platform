from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional

import models
from database import get_db, engine
from auth import (
    authenticate_user, create_access_token, get_password_hash,
    generate_and_send_sms_code, verify_sms_code, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secret Code + SMS 2FA Auth")


# Регистрация
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Проверяем существование пользователя (используем новые функции)
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    if get_user_by_phone(db, user_data.phone):
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")

    # Создаем пользователя
    hashed_password = get_password_hash(user_data.password)
    hashed_secret_code = get_password_hash(user_data.secret_code)

    new_user = models.User(
        email=user_data.email,
        phone=user_data.phone,
        secret_code=hashed_secret_code,
        hashed_password=hashed_password,
        is_2fa_enabled=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Пользователь зарегистрирован",
        "user_id": new_user.id,
        "instruction": "Для входа используйте email и ваш секретный код"
    }

# Первый этап аутентификации
@app.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    # В нашей схеме:
    # username = email
    # password = секретный код пользователя

    user = authenticate_user(db, form_data.username, form_data.password)
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
@app.post("/verify-2fa")
async def verify_2fa(
        request: Verify2FARequest,
        db: Session = Depends(get_db)
):
    # Проверяем SMS код
    is_valid = verify_sms_code(db, request.user_id, request.sms_code)
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
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# Защищенный эндпоинт
@app.get("/protected-data")
async def protected_data(current_user: models.User = Depends(get_current_user)):
    return {
        "message": "Доступ к защищенным данным разрешен",
        "user_id": current_user.id,
        "email": current_user.email,
        "data": "Ваши секретные данные здесь"
    }


# Повторная отправка SMS кода
@app.post("/resend-sms")
async def resend_sms(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await generate_and_send_sms_code(db, user)

    return {"message": "Новый SMS код отправлен"}