# src/endpoints/likes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.database.models import User
from src.repository.likes_repository import likes_repository

likes_router = APIRouter(prefix="/likes", tags=["likes"])

@likes_router.post("/posts/{post_id}")
async def toggle_post_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поставить/убрать лайк посту - возвращает текущее состояние"""
    try:
        result = await likes_repository.toggle_like(db, current_user.id, post_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@likes_router.get("/posts/{post_id}/count")
async def get_post_likes_count(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить общее количество лайков поста (для всех пользователей)"""
    count = await likes_repository.get_likes_count(db, post_id)
    return {"post_id": post_id, "likes_count": count}