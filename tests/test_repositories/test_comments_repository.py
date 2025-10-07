# src/tests/test_repositories/test_comments_repository.py
import pytest
from src.repository.comments_repository import comments_repository
from src.schemas.project import CommentCreate


class TestCommentsRepository:
    @pytest.mark.asyncio
    async def test_create_comment(self, db_session, test_user, test_post):
        """Тест создания комментария"""
        comment_data = CommentCreate(
            content="Test comment",
            post_id=test_post.id
        )

        comment = await comments_repository.create(
            db_session,
            comment_data,
            user_id=test_user.id  # Явно передаем user_id
        )

        print(f"🔍 Created comment: id={comment.id}, user_id={comment.user_id}")

        assert comment.id is not None
        assert comment.content == "Test comment"
        assert comment.user_id == test_user.id  # Проверяем что user_id установился
        assert comment.post_id == test_post.id

    @pytest.mark.asyncio
    async def test_get_by_post(self, db_session, test_user, test_post):
        """Тест получения комментариев поста"""
        # Создаем 3 комментария
        for i in range(3):
            comment_data = CommentCreate(
                content=f"Comment {i}",
                post_id=test_post.id
            )
            comment = await comments_repository.create(
                db_session,
                comment_data,
                user_id=test_user.id
            )
            print(f"🔍 Created comment {i}: id={comment.id}")

        comments = await comments_repository.get_by_post(db_session, test_post.id)
        print(f"🔍 Retrieved {len(comments)} comments")

        assert len(comments) == 3
        assert all(c.post_id == test_post.id for c in comments)
        assert all(c.user_id == test_user.id for c in comments)

    @pytest.mark.asyncio
    async def test_get_by_post_pagination(self, db_session, test_user, test_post):
        """Тест пагинации комментариев"""
        for i in range(5):
            comment_data = CommentCreate(
                content=f"Comment {i}",
                user_id=test_user.id,
                post_id=test_post.id
            )
            await comments_repository.create(db_session, comment_data)

        comments = await comments_repository.get_by_post(
            db_session, test_post.id, skip=2, limit=2
        )
        assert len(comments) == 2

# pytest tests/test_repositories/test_comments_repository.py -v --html=report.html
