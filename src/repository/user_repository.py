# src/repository/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

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

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[models.User]:
        """Получение пользователя по username"""
        result = await db.execute(
            select(models.User).where(models.User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_user(self, db: AsyncSession, user_id: int, update_data: dict) -> Optional[models.User]:
        """Обновление данных пользователя"""
        user = await self.get_user_by_id(db, user_id)
        if user:
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            await db.commit()
            await db.refresh(user)
        return user

    async def get_users_by_ids(self, db: AsyncSession, user_ids: List[int]) -> List[models.User]:
        """Получение списка пользователей по IDs"""
        if not user_ids:
            return []

        result = await db.execute(
            select(models.User).where(models.User.id.in_(user_ids))
        )
        return result.scalars().all()

    async def search_users(self, db: AsyncSession, query: str, limit: int = 10) -> List[models.User]:
        """Поиск пользователей по email, username или phone"""
        result = await db.execute(
            select(models.User).where(
                (models.User.email.ilike(f"%{query}%")) |
                (models.User.username.ilike(f"%{query}%")) |
                (models.User.phone.ilike(f"%{query}%"))
            ).limit(limit)
        )
        return result.scalars().all()

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> bool:
        """Деактивация пользователя"""
        user = await self.get_user_by_id(db, user_id)
        if user:
            user.is_active = False
            await db.commit()
            return True
        return False

    async def activate_user(self, db: AsyncSession, user_id: int) -> bool:
        """Активация пользователя"""
        user = await self.get_user_by_id(db, user_id)
        if user and not user.is_active:
            user.is_active = True
            await db.commit()
            return True
        return False


user_repository = UserRepository()