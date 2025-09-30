# src/schemas/__init__.py
from datetime import datetime
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Базовая схема ответа"""
    success: bool = True
    message: Optional[str] = None

class PaginatedResponse(BaseResponse, Generic[T]):
    """Схема для пагинированных ответов"""
    data: list[T]
    total: int
    page: int
    size: int
    pages: int

class TokenData(BaseModel):
    """Данные JWT токена"""
    user_id: int
    email: str
    exp: datetime

# Re-export всех схем
from .auth import *
from .user import *
from .project import *
from .webinar import *
from .payment import *
from .notification import *