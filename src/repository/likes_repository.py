# src/repository/likes_repository.py
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Like


class LikesRepository:
    def __init__(self):
        self.model = Like

    async def create(self, db: AsyncSession, user_id: int, post_id: int) -> Like:
        like = Like(user_id=user_id, post_id=post_id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return like

    async def delete(self, db: AsyncSession, user_id: int, post_id: int) -> bool:
        stmt = delete(Like).where(
            (Like.user_id == user_id) &
            (Like.post_id == post_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def get_by_post(self, db: AsyncSession, post_id: int) -> List[Like]:
        stmt = select(Like).where(Like.post_id == post_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def user_has_liked(self, db: AsyncSession, user_id: int, post_id: int) -> bool:
        stmt = select(Like).where(
            (Like.user_id == user_id) &
            (Like.post_id == post_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

likes_repository = LikesRepository()