# src/repository/comments_repository.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models.models_content import Comment
from src.schemas.project import CommentCreate, CommentUpdate

class CommentsRepository(BaseRepository[Comment, CommentCreate, CommentUpdate]):
    def __init__(self):
        super().__init__(Comment)

    async def get_by_post(
        self,
        db: AsyncSession,
        post_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

comments_repository = CommentsRepository()