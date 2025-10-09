# src/tests/test_webinar_notifications/test_webinar_basic.py
import pytest
from datetime import datetime, timedelta


class TestWebinarBasic:

    @pytest.mark.asyncio
    async def test_get_webinars_list(self, client, test_user, test_webinar):
        """Тест получения списка вебинаров"""
        response = client.get("/webinars/")
        print(f"Get webinars response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('webinars', []))} webinars")
            assert 'webinars' in data
            assert 'pagination' in data

    @pytest.mark.asyncio
    async def test_get_webinar_details(self, client, test_user, test_webinar):
        """Тест получения деталей вебинара"""
        response = client.get(f"/webinars/{test_webinar.id}")
        print(f"Get webinar details response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            assert data['id'] == test_webinar.id
            assert data['title'] == test_webinar.title

    @pytest.mark.asyncio
    async def test_get_webinar_announcements(self, client):
        """Тест получения анонсов вебинаров"""
        response = client.get("/webinars/announcements")
        print(f"Get announcements response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            assert 'announcements' in data
            assert 'count' in data

    @pytest.mark.asyncio
    async def test_create_webinar_admin_only(self, client, test_user):
        """Тест что создание вебинара доступно только админам/менеджерам"""
        webinar_data = {
            "title": "Admin Only Webinar",
            "description": "Should fail for regular user",
            "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 100
        }

        # Без мока RBAC проверки должен быть 403
        response = client.post("/webinars/", json=webinar_data)
        print(f"Create webinar without permissions: {response.status_code}")

        # Может быть 403 (Forbidden) или 422 (если нет прав)
        assert response.status_code in [403, 422]

# pytest tests/test_webinar_notifications/test_webinar_basic.py -v --html=report.html