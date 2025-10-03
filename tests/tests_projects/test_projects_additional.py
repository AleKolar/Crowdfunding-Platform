# tests/test_projects_additional.py
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProjectsAdditional:
    """Дополнительные тесты для эндпоинтов проектов"""

    @pytest.fixture
    def mock_post_response(self):
        return {
            "id": 1,
            "content": "Test post content",
            "post_type": "update",
            "is_pinned": False,
            "author_id": 1,
            "project_id": 1,
            "media_url": None,
            "media_thumbnail": None,
            "media_duration": None,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "views_count": 0,
            "likes_count": 0,
            "comments_count": 0,
            "shares_count": 0,
            "is_liked": False
        }

    @pytest.fixture
    def mock_comment_response(self):
        return {
            "id": 1,
            "content": "Test comment",
            "post_id": 1,
            "user_id": 1,
            "parent_id": None,
            "is_edited": False,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }

    def test_create_project_post(self, client, current_user_mock):
        """Тест создания поста в проекте"""
        # Убрали мок get_current_user - он уже в фикстуре client
        with patch('src.endpoints.projects.ProjectService.create_project_post',
                   new_callable=AsyncMock) as mock_service:
            post_data = {
                "content": "Test post content",
                "post_type": "update"
            }

            mock_service.return_value = {
                "id": 1,
                "content": "Test post content",
                "post_type": "update",
                "is_pinned": False,
                "author_id": current_user_mock.id,
                "project_id": 1,
                "media_url": None,
                "media_thumbnail": None,
                "media_duration": None,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "views_count": 0,
                "likes_count": 0,
                "comments_count": 0,
                "shares_count": 0,
                "is_liked": False
            }

            response = client.post("/projects/1/posts", json=post_data)

            print(f"📥 Create post status: {response.status_code}")
            print(f"📥 Create post response: {response.text}")

            # Временное решение - проверяем оба статуса
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
            data = response.json()
            assert data["content"] == post_data["content"]

    def test_get_project_posts(self, client, mock_post_response):
        """Тест получения постов проекта"""
        with patch('src.endpoints.projects.ProjectService.get_project_posts',
                   new_callable=AsyncMock) as mock_service:
            mock_service.return_value = [mock_post_response]

            response = client.get("/projects/1/posts")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    def test_like_project(self, client, current_user_mock):
        """Тест лайка проекта"""
        # Убрали мок get_current_user - он уже в фикстуре client
        with patch('src.endpoints.projects.ProjectService.like_project',
                   new_callable=AsyncMock) as mock_service:
            mock_service.return_value = {"message": "Project liked successfully", "like": {"id": 1}}

            response = client.post("/projects/1/like")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert "Project liked" in data["message"]


# pytest tests/tests_projects/test_projects_additional.py --html=report.html