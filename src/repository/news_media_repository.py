# src/repository/news_media_repository.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import UpdateMedia
from src.schemas.project import NewsMediaCreate, NewsMediaUpdate

class NewsMediaRepository(BaseRepository[UpdateMedia, NewsMediaCreate, NewsMediaUpdate]):
    def __init__(self):
        super().__init__(UpdateMedia)

    async def get_by_update(
        self,
        db: AsyncSession,
        update_id: int
    ) -> List[UpdateMedia]:
        # !!! Упрощенная версия через get_by_field из base.py !!!
        return await self.get_by_field(
            db,
            field_name='update_id',
            field_value=update_id
        )

news_media_repository = NewsMediaRepository()