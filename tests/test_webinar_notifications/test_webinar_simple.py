# tests/test_webinar_notifications/test_webinar_simple.py
import pytest
from datetime import datetime, timedelta


class TestWebinarSimple:

    @pytest.mark.asyncio
    async def test_webinar_list(self, client, test_webinar):
        """Простой тест списка вебинаров"""
        print("\n🔍 Testing webinar list endpoint")
        response = client.get("/webinars/")
        print(f"  Status: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")

    @pytest.mark.asyncio
    async def test_webinar_announcements(self, client):
        """Простой тест анонсов"""
        print("\n🔍 Testing webinar announcements endpoint")
        response = client.get("/webinars/announcements")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Found {data.get('count', 0)} announcements")

    @pytest.mark.asyncio
    async def test_webinar_detail(self, client, test_webinar):
        """Простой тест деталей вебинара"""
        print(f"\n🔍 Testing webinar detail for id {test_webinar.id}")
        response = client.get(f"/webinars/{test_webinar.id}")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Webinar: {data.get('title')}")

# pytest tests/test_webinar_notifications/test_webinar_simple.py -v --html=report.html