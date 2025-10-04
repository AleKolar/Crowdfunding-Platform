# src/repository/project_news_repository.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import ProjectUpdate
from src.schemas.project import ProjectNewsCreate, ProjectNewsUpdate

class ProjectNewsRepository(BaseRepository[ProjectUpdate, ProjectNewsCreate, ProjectNewsUpdate]):
    def __init__(self):
        super().__init__(ProjectUpdate)

    async def get_by_project(
        self,
        db: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProjectUpdate]:
        # !!! Упрощенная версия через get_by_field из base.py !!!
        return await self.get_by_field(
            db,
            field_name='project_id',
            field_value=project_id,
            order_by=ProjectUpdate.created_at.desc(),
            skip=skip,
            limit=limit
        )

project_news_repository = ProjectNewsRepository()