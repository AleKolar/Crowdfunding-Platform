# src/repository/projects_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.base import BaseRepository
from src.database.models.models_content import Project, ProjectStatus
from src.schemas.project import ProjectCreate, ProjectUpdate


class ProjectsRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(Project)

    async def get_by_creator(
            self,
            db: AsyncSession,
            creator_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Project]:
        """ Получение проектов создателя """
        return await self.get_by_field(
            db,
            field_name='creator_id',
            field_value=creator_id,
            order_by=Project.created_at.desc(),
            skip=skip,
            limit=limit
        )

    async def get_with_filters(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            status: Optional[ProjectStatus] = None,
            is_featured: Optional[bool] = None,
            min_goal: Optional[float] = None,
            max_goal: Optional[float] = None
    ) -> List[Project]:
        """Исправленная версия с правильной фильтрацией в БД"""
        from sqlalchemy import and_, select

        # Начинаем с базового запроса
        conditions = []

        # Добавляем условия фильтрации
        if category:
            conditions.append(self.model.category == category)
        if status:
            conditions.append(self.model.status == status)
        if is_featured is not None:
            conditions.append(self.model.is_featured == is_featured)
        if min_goal is not None:
            conditions.append(self.model.goal_amount >= min_goal)
        if max_goal is not None:
            conditions.append(self.model.goal_amount <= max_goal)

        # Собираем запрос
        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def search(
            self,
            db: AsyncSession,
            query: str,
            skip: int = 0,
            limit: int = 100
    ) -> List[Project]:
        # Используем универсальный поиск
        return await self.search_in_fields(
            db,
            search_query=query,
            search_fields=['title', 'description', 'short_description'],
            skip=skip,
            limit=limit
        )

    async def increment_views(self, db: AsyncSession, project_id: int) -> None:
        # Используем универсальный метод
        await self.increment_field(db, project_id, 'views_count')

    async def get_with_media(self, db: AsyncSession, project_id: int) -> Optional[Project]:
        # Используем универсальный метод с отношениями
        return await self.get_with_relationships(db, project_id, ['media'])


projects_repository = ProjectsRepository()