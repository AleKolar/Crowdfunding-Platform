# src/repository/posts_repository.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import Post
from src.schemas.project import PostCreate, PostUpdate


class PostsRepository(BaseRepository[Post, PostCreate, PostUpdate]):
    def __init__(self):
        super().__init__(Post)

    async def get_by_project(
        self,
        db: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Post]:
        # !!! Упрощенная версия через get_by_field из base.py !!!
        return await self.get_by_field(
            db,
            field_name='project_id',
            field_value=project_id,
            order_by=Post.created_at.desc(),
            skip=skip,
            limit=limit
        )

posts_repository = PostsRepository()