# src/repository/comments_repository.py
from typing import List
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
        # !!! Упрощенная версия через get_by_field из base.py !!!
        return await self.get_by_field(
            db,
            field_name='post_id',
            field_value=post_id,
            order_by=Comment.created_at.desc(),
            skip=skip,
            limit=limit
        )

comments_repository = CommentsRepository()