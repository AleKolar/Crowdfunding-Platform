# src/repository/base.py
from typing import List, Optional, Any, TypeVar, Generic
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Project

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List[Project]:
        """Получение всех проектов (базовый метод)"""
        from sqlalchemy import select

        query = select(self.model).where(
            self.model.is_active == True
        ).order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_multi(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            **filters
    ) -> List[ModelType]:
        stmt = select(self.model)

        filter_conditions = []
        for field, value in filters.items():
            if value is not None:
                if isinstance(value, (list, tuple)):
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
        create_data = obj_in.model_dump()
        create_data.update(extra_data)
        db_obj = self.model(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db: AsyncSession,
            db_obj: ModelType,
            obj_in: UpdateSchemaType
    ) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False

    async def get_by_field(
            self,
            db: AsyncSession,
            field_name: str,
            field_value: Any,
            order_by: Optional[Any] = None,
            skip: int = 0,
            limit: int = 100,
            **additional_filters
    ) -> List[ModelType]:
        """Универсальный метод для получения по полю с фильтрацией и сортировкой"""
        stmt = select(self.model).where(getattr(self.model, field_name) == field_value)

        # Дополнительные фильтры
        for filter_field, filter_value in additional_filters.items():
            if filter_value is not None:
                stmt = stmt.where(getattr(self.model, filter_field) == filter_value)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_in_fields(
            self,
            db: AsyncSession,
            search_query: str,
            search_fields: List[str],
            skip: int = 0,
            limit: int = 100,
            **filters
    ) -> List[ModelType]:
        """Универсальный поиск по нескольким полям"""
        search_conditions = []
        for field in search_fields:
            search_conditions.append(getattr(self.model, field).ilike(f"%{search_query}%"))

        stmt = select(self.model).where(and_(*search_conditions))

        # Дополнительные фильтры
        filter_conditions = []
        for field, value in filters.items():
            if value is not None:
                filter_conditions.append(getattr(self.model, field) == value)

        if filter_conditions:
            stmt = stmt.where(and_(*filter_conditions))

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def increment_field(
            self,
            db: AsyncSession,
            id: int,
            field_name: str,
            increment: int = 1
    ) -> None:
        """Увеличение числового поля"""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values({field_name: getattr(self.model, field_name) + increment})
        )
        await db.execute(stmt)
        await db.commit()

    async def get_with_relationships(
            self,
            db: AsyncSession,
            id: int,
            relationship_names: List[str]
    ) -> Optional[ModelType]:
        """Получение объекта с отношениями"""
        stmt = select(self.model).where(self.model.id == id)

        # Динамическая загрузка отношений
        for rel_name in relationship_names:
            stmt = stmt.options(selectinload(getattr(self.model, rel_name)))

        result = await db.execute(stmt)
        return result.scalar_one_or_none()