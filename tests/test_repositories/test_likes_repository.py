# src/tests/test_repositories/test_likes_repository.py
import pytest
from src.repository.likes_repository import likes_repository


class TestLikesRepository:
    @pytest.mark.asyncio
    async def test_create_like(self, db_session, test_user, test_post):
        """Тест создания лайка"""
        like = await likes_repository.create(db_session, test_user.id, test_post.id)
        assert like.id is not None
        assert like.user_id == test_user.id
        assert like.post_id == test_post.id

    @pytest.mark.asyncio
    async def test_create_duplicate_like(self, db_session, test_user, test_post):
        """Тест создания дубликата лайка"""
        await likes_repository.create(db_session, test_user.id, test_post.id)

        with pytest.raises(ValueError, match="User already liked this post"):
            await likes_repository.create(db_session, test_user.id, test_post.id)

    @pytest.mark.asyncio
    async def test_delete_like(self, db_session, test_user, test_post):
        """Тест удаления лайка"""
        like = await likes_repository.create(db_session, test_user.id, test_post.id)

        result = await likes_repository.delete(db_session, test_user.id, test_post.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_user_has_liked(self, db_session, test_user, test_post):
        """Тест проверки лайка пользователя"""
        has_liked = await likes_repository.user_has_liked(db_session, test_user.id, test_post.id)
        assert has_liked is False

        await likes_repository.create(db_session, test_user.id, test_post.id)

        has_liked = await likes_repository.user_has_liked(db_session, test_user.id, test_post.id)
        assert has_liked is True

    @pytest.mark.asyncio
    async def test_get_likes_count(self, db_session, test_user, test_post):
        """Тест подсчета лайков"""
        for user_id in [test_user.id]:  # Можно добавить больше пользователей
            await likes_repository.create(db_session, user_id, test_post.id)

        count = await likes_repository.get_likes_count(db_session, test_post.id)
        assert count >= 1

    @pytest.mark.asyncio
    async def test_toggle_like(self, db_session, test_user, test_post):
        """Тест переключения лайка"""
        result1 = await likes_repository.toggle_like(db_session, test_user.id, test_post.id)
        assert result1["action"] == "liked"
        assert result1["liked"] is True

        result2 = await likes_repository.toggle_like(db_session, test_user.id, test_post.id)
        assert result2["action"] == "unliked"
        assert result2["liked"] is False

# pytest tests/test_repositories/test_likes_repository.py -v --html=report.html