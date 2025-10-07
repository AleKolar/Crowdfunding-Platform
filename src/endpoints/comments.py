# src/endpoints/comments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.database.models import User
from src.repository.comments_repository import comments_repository
from src.schemas.project import CommentCreate, CommentResponse

comments_router = APIRouter(prefix="/comments", tags=["comments"])


@comments_router.post("/", response_model=CommentResponse)
async def create_comment(
        comment_data: CommentCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание комментария"""
    from src.database.models.models_content import Comment

    comment = Comment(
        content=comment_data.content,
        post_id=comment_data.post_id,
        user_id=current_user.id,
        parent_id=comment_data.parent_id
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@comments_router.get("/post/{post_id}", response_model=list[CommentResponse])
async def get_post_comments(
        post_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получение комментариев поста"""
    return await comments_repository.get_by_post(db, post_id, skip, limit)


@comments_router.delete("/{comment_id}")
async def delete_comment(
        comment_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаление комментария (только свой)"""
    comment = await comments_repository.get(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")

    await comments_repository.delete(db, comment_id)
    return {"message": "Comment deleted"}