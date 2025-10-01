# src/repository/news_media_repository.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import UpdateMedia
from src.schemas.project import NewsMediaCreate, NewsMediaUpdate  # ← ИЗМЕНЕНО

class NewsMediaRepository(BaseRepository[UpdateMedia, NewsMediaCreate, NewsMediaUpdate]):  # ← ИЗМЕНЕНО
    def __init__(self):
        super().__init__(UpdateMedia)

    async def get_by_update(
        self,
        db: AsyncSession,
        update_id: int
    ) -> List[UpdateMedia]:
        stmt = select(UpdateMedia).where(UpdateMedia.update_id == update_id)
        result = await db.execute(stmt)
        return result.scalars().all()

news_media_repository = NewsMediaRepository()  # ← ИЗМЕНЕНО