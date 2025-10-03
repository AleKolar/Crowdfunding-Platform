# src/repository/base.py
from typing import List, Optional, TypeVar, Generic, Dict, Any
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from fastapi import HTTPException, status
from src.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый репозиторий с улучшенной обработкой ошибок и фильтрацией"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: int, detail: str = None) -> ModelType:
        """Получение объекта или вызов 404 ошибки"""
        obj = await self.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail or f"{self.model.__name__} with id {id} not found"
            )
        return obj

    async def get_multi(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            **filters
    ) -> List[ModelType]:
        stmt = select(self.model)

        # Улучшенная фильтрация
        filter_conditions = []
        for field, value in filters.items():
            if value is not None:
                if isinstance(value, (list, tuple)):
                    # Для фильтрации по списку значений
                    filter_conditions.append(getattr(self.model, field).in_(value))
                else:
                    filter_conditions.append(getattr(self.model, field) == value)

        if filter_conditions:
            stmt = stmt.where(and_(*filter_conditions))

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(
            self,
            db: AsyncSession,
            obj_in: CreateSchemaType,
            **extra_data
    ) -> ModelType:
        """Создание с обработкой транзакций"""
        try:
            create_data = obj_in.model_dump()
            create_data.update(extra_data)
            db_obj = self.model(**create_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating {self.model.__name__}: {str(e)}"
            )

    async def update(
            self,
            db: AsyncSession,
            id: int,
            obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Обновление с обработкой транзакций"""
        try:
            update_data = obj_in.model_dump(exclude_unset=True)
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating {self.model.__name__}: {str(e)}"
            )

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Удаление с обработкой транзакций"""
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting {self.model.__name__}: {str(e)}"
            )