# src/tests/test_repositories/test_likes_repository.py (UNIT тесты)
import pytest

from src.repository.likes_repository import likes_repository


@pytest.mark.asyncio
async def test_toggle_like_complex_logic(db_session, test_user, test_post):
    """Тестируем сложную логику переключения лайков"""
    result1 = await likes_repository.toggle_like(db_session, test_user.id, test_post.id)
    assert result1["action"] == "liked"

    result2 = await likes_repository.toggle_like(db_session, test_user.id, test_post.id)
    assert result2["action"] == "unliked"


# tests/test_api/test_likes_endpoints.py (API тесты)
def test_like_post_endpoint(client, authenticated_headers, test_post):
    """Тестируем эндпоинт лайков"""
    response = client.post(f"/likes/posts/{test_post.id}", headers=authenticated_headers)
    assert response.status_code == 200
    assert response.json()["action"] == "liked"

# pytest tests/test_repositories/test_likes_repository.py --html=report.html