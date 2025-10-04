# src/repository/likes_repository.py
from typing import List, Dict, Any
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Like


class LikesRepository:
    def __init__(self):
        self.model = Like

    async def create(self, db: AsyncSession, user_id: int, post_id: int) -> Like:
        """Создание лайка с проверкой на дубликат"""
        # Сначала проверяем, не существует ли уже лайк
        existing_like = await self.user_has_liked(db, user_id, post_id)
        if existing_like:
            raise ValueError("User already liked this post")

        like = Like(user_id=user_id, post_id=post_id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return like

    async def delete(self, db: AsyncSession, user_id: int, post_id: int) -> bool:
        """Удаление лайка по user_id и post_id"""
        stmt = delete(Like).where(
            and_(Like.user_id == user_id, Like.post_id == post_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def get_by_post(self, db: AsyncSession, post_id: int) -> List[Like]:
        """Получение всех лайков поста"""
        stmt = select(Like).where(Like.post_id == post_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Like]:
        """Получение лайков пользователя с пагинацией"""
        stmt = (
            select(Like)
            .where(Like.user_id == user_id)
            .order_by(Like.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def user_has_liked(self, db: AsyncSession, user_id: int, post_id: int) -> bool:
        """Проверка, поставил ли пользователь лайк посту"""
        stmt = select(Like).where(
            and_(Like.user_id == user_id, Like.post_id == post_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_likes_count(self, db: AsyncSession, post_id: int) -> int:
        """Получение количества лайков поста"""
        stmt = select(Like).where(Like.post_id == post_id)
        result = await db.execute(stmt)
        return len(result.scalars().all())

    async def get_user_likes_count(self, db: AsyncSession, user_id: int) -> int:
        """Получение количества лайков пользователя"""
        stmt = select(Like).where(Like.user_id == user_id)
        result = await db.execute(stmt)
        return len(result.scalars().all())

    async def toggle_like(self, db: AsyncSession, user_id: int, post_id: int) -> Dict[str, Any]:
        """Переключение лайка (поставить/убрать)"""
        has_liked = await self.user_has_liked(db, user_id, post_id)

        if has_liked:
            await self.delete(db, user_id, post_id)
            return {"action": "unliked", "liked": False}
        else:
            like = await self.create(db, user_id, post_id)
            return {"action": "liked", "liked": True, "like": like}

    async def get_popular_posts(self, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение самых популярных постов по количеству лайков"""
        from sqlalchemy import func
        stmt = (
            select(Like.post_id, func.count(Like.id).label('likes_count'))
            .group_by(Like.post_id)
            .order_by(func.count(Like.id).desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [{"post_id": row.post_id, "likes_count": row.likes_count} for row in result]

    async def get_likes_stats(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Получение статистики лайков пользователя"""
        total_likes = await self.get_user_likes_count(db, user_id)

        # Получаем посты с наибольшим количеством лайков от пользователя
        stmt = (
            select(Like.post_id)
            .where(Like.user_id == user_id)
            .group_by(Like.post_id)
            .order_by(Like.created_at.desc())
            .limit(5)
        )
        result = await db.execute(stmt)
        recent_liked_posts = [row.post_id for row in result]

        return {
            "total_likes_given": total_likes,
            "recent_liked_posts": recent_liked_posts,
            "likes_per_day_avg": total_likes / 30  # Примерная средняя за месяц
        }


likes_repository = LikesRepository()