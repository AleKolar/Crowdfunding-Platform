from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional



# Pydantic модели
class UserRegister(BaseModel):
    email: EmailStr
    phone: str
    secret_code: str  # Статический код пользователя
    password: str

class LoginResponse(BaseModel):
    requires_2fa: bool = True
    message: str
    user_id: int

class Verify2FARequest(BaseModel):
    user_id: int
    sms_code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int