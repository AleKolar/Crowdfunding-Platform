# src/tests/test_comments/test_comments_endpoints.py
from fastapi import status


class TestCommentsEndpoints:
    def test_create_comment(self, client, authenticated_headers, test_post):
        response = client.post("/comments/", json={
            "content": "Test comment content",
            "post_id": test_post.id
        }, headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Test comment content"
        assert data["post_id"] == test_post.id
        assert "user_id" in data

    def test_get_post_comments(self, client, authenticated_headers, test_post):
        # Сначала создаем комментарий
        client.post("/comments/", json={
            "content": "Test comment",
            "post_id": test_post.id
        }, headers=authenticated_headers)

        # Получаем комментарии поста
        response = client.get(f"/comments/post/{test_post.id}")
        assert response.status_code == status.HTTP_200_OK
        comments = response.json()
        assert len(comments) == 1
        assert comments[0]["content"] == "Test comment"

# pytest tests/test_comments/test_comments_endpoints.py --html=report.html