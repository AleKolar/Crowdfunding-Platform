# src/repository/projects_repository.py
from typing import List, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        stmt = (
            select(Project)
            .where(Project.creator_id == creator_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Project)

        filters = []
        if category:
            filters.append(Project.category == category)
        if status:
            filters.append(Project.status == status)
        if is_featured is not None:
            filters.append(Project.is_featured == is_featured)
        if min_goal is not None:
            filters.append(Project.goal_amount >= min_goal)
        if max_goal is not None:
            filters.append(Project.goal_amount <= max_goal)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Project.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        stmt = (
            select(Project)
            .where(
                (Project.title.ilike(f"%{query}%")) |
                (Project.description.ilike(f"%{query}%")) |
                (Project.short_description.ilike(f"%{query}%"))
            )
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def increment_views(self, db: AsyncSession, project_id: int) -> None:
        """Увеличение счетчика просмотров"""
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(views_count=Project.views_count + 1)
        )
        await db.execute(stmt)
        await db.commit()

    async def get_with_media(self, db: AsyncSession, project_id: int) -> Optional[Project]:
        """Получение проекта с медиафайлами"""
        stmt = (
            select(Project)
            .options(selectinload(Project.media))
            .where(Project.id == project_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Синглтон экземпляр
projects_repository = ProjectsRepository()
