# src/tests/test_repositories/test_posts_repository.py
import pytest
from src.repository.posts_repository import posts_repository
from src.schemas.project import PostCreate
from src.database.models.models_content import PostType


class TestPostsRepository:
    @pytest.mark.asyncio
    async def test_create_post(self, db_session, test_user, test_project):
        """Тест создания поста"""
        # ✅ Из Pydantic
        post_data = PostCreate(
            content="Test Content",
            author_id=test_user.id,
            project_id=test_project.id
        )

        # !!! ✅ Передаем post_type как extra_data в create в src/repository/base.py
        post = await posts_repository.create(
            db_session,
            post_data,
            post_type=PostType.UPDATE
        )

        assert post.id is not None
        assert post.content == "Test Content"
        assert post.project_id == test_project.id
        assert post.post_type == PostType.UPDATE

    @pytest.mark.asyncio
    async def test_get_by_project(self, db_session, test_user, test_project):
        """Тест получения постов проекта"""
        for i in range(3):
            post_data = PostCreate(
                content=f"Content {i}",
                author_id=test_user.id,
                project_id=test_project.id
            )

            await posts_repository.create(
                db_session,
                post_data,
                post_type=PostType.UPDATE
            )

        posts = await posts_repository.get_by_project(db_session, test_project.id)
        assert len(posts) == 3
        assert all(p.project_id == test_project.id for p in posts)

# pytest tests/test_repositories/test_posts_repository.py -v --html=report.html