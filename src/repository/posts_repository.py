# src/repository/posts_repository.py
from typing import List
from sqlalchemy import select
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
        stmt = (
            select(Post)
            .where(Post.project_id == project_id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

posts_repository = PostsRepository()