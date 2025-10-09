# src/repository/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.database import models


class UserRepository:

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[models.User]:
        """Получение пользователя по ID"""
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[models.User]:
        """Получение пользователя по email"""
        result = await db.execute(
            select(models.User).where(models.User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, db: AsyncSession, phone: str) -> Optional[models.User]:
        """Получение пользователя по телефону"""
        result = await db.execute(
            select(models.User).where(models.User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user_data: dict) -> models.User:
        """Создание нового пользователя"""
        user = models.User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(self, db: AsyncSession, user_id: int, update_data: dict) -> Optional[models.User]:
        """Обновление данных пользователя"""
        user = await self.get_user_by_id(db, user_id)
        if user:
            for field, value in update_data.items():
                setattr(user, field, value)
            await db.commit()
            await db.refresh(user)
        return user


user_repository = UserRepository()