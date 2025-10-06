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
        # Упрощенная версия
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
        # Используем get_multi с фильтрами
        filters = {}
        if category: filters['category'] = category
        if status: filters['status'] = status
        if is_featured is not None: filters['is_featured'] = is_featured

        projects = await self.get_multi(db, skip=skip, limit=limit, **filters)

        # Дополнительная фильтрация по диапазону (не поддерживается get_multi)
        if min_goal is not None:
            projects = [p for p in projects if p.goal_amount >= min_goal]
        if max_goal is not None:
            projects = [p for p in projects if p.goal_amount <= max_goal]

        return projects

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