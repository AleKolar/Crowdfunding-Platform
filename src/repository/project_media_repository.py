from typing import List, Optional
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
        # !!! Используем универсальный метод вместо дублирования get_by_field из base!!!
        additional_filters = {}
        if media_type:
            additional_filters['file_type'] = media_type

        return await self.get_by_field(
            db,
            field_name='project_id',
            field_value=project_id,
            order_by=(ProjectMedia.sort_order, ProjectMedia.created_at),
            skip=skip,
            limit=limit,
            **additional_filters
        )


project_media_repository = ProjectMediaRepository()