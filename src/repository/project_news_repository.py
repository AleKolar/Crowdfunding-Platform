# src/repository/project_news_repository.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import ProjectUpdate
from src.schemas.project import ProjectNewsCreate, ProjectNewsUpdate  # ← ИЗМЕНЕНО

class ProjectNewsRepository(BaseRepository[ProjectUpdate, ProjectNewsCreate, ProjectNewsUpdate]):  # ← ИЗМЕНЕНО
    def __init__(self):
        super().__init__(ProjectUpdate)

    async def get_by_project(
        self,
        db: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProjectUpdate]:
        stmt = (
            select(ProjectUpdate)
            .where(ProjectUpdate.project_id == project_id)
            .order_by(ProjectUpdate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

project_news_repository = ProjectNewsRepository()  # ← ИЗМЕНЕНО