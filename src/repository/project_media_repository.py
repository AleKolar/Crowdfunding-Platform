# src/repository/project_media_repository.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import ProjectMedia
from src.schemas.project import ProjectMediaCreate, ProjectMediaUpdate


class ProjectMediaRepository(BaseRepository[ProjectMedia, ProjectMediaCreate, ProjectMediaUpdate]):
    def __init__(self):
        super().__init__(ProjectMedia)

    async def get_by_project(
            self,
            db: AsyncSession,
            project_id: int,
            media_type: Optional[str] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[ProjectMedia]:
        stmt = select(ProjectMedia).where(ProjectMedia.project_id == project_id)

        if media_type:
            stmt = stmt.where(ProjectMedia.file_type == media_type)

        stmt = stmt.order_by(ProjectMedia.sort_order, ProjectMedia.created_at)
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()


project_media_repository = ProjectMediaRepository()