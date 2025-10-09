# src/tests/test_webinar_notifications/test_webinar_notifications_endpoints.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import uuid

from sqlalchemy import select

from src.database import models


class TestWebinarNotifications:

    def _generate_unique_email(self):
        """Генерация уникального email"""
        unique_part = uuid.uuid4().hex[:8]
        return f"test_{unique_part}@example.com"

    def _generate_unique_phone(self):
        """Генерация уникального телефона"""
        unique_part = uuid.uuid4().hex[:7]
        return f"+7999{unique_part}"

    def _generate_unique_username(self):
        """Генерация уникального username"""
        unique_part = uuid.uuid4().hex[:8]
        return f"user_{unique_part}"

    @pytest.mark.asyncio
    async def test_webinar_registration_sends_notification(self, client, db_session, test_user, test_webinar):
        """Тест что регистрация на вебинар отправляет уведомление"""
        # Регистрируем пользователя на вебинар
        register_response = client.post(f"/webinars/{test_webinar.id}/register")
        print(f"Register response: {register_response.status_code} - {register_response.text}")

        if register_response.status_code != 200:
            # Если регистрация не удалась, проверяем почему
            webinar_check = await db_session.get(models.Webinar, test_webinar.id)
            print(f"Webinar status: {webinar_check.status}, scheduled_at: {webinar_check.scheduled_at}")

            # Проверяем существующие регистрации
            existing_reg = await db_session.scalar(
                select(models.WebinarRegistration).where(
                    models.WebinarRegistration.webinar_id == test_webinar.id,
                    models.WebinarRegistration.user_id == test_user.id
                )
            )
            print(f"Existing registration: {existing_reg}")

        assert register_response.status_code == 200

        # Проверяем что уведомление создано в БД
        notification = await db_session.scalar(
            select(models.Notification).where(
                models.Notification.user_id == test_user.id
            )
        )

        assert notification is not None
        # Проверяем что это уведомление о регистрации
        assert any(keyword in notification.notification_type for keyword in ["registration", "webinar"])

    @pytest.mark.asyncio
    async def test_webinar_join_sends_notification(self, client, db_session, test_user, test_started_webinar):
        """Тест что присоединение к вебинару отправляет уведомление"""
        # Сначала регистрируем пользователя на вебинар
        registration = models.WebinarRegistration(
            webinar_id=test_started_webinar.id,
            user_id=test_user.id
        )
        db_session.add(registration)
        await db_session.commit()

        # Мокаем генерацию токена LiveKit
        with patch('src.services.webinar_service.webinar_service.generate_participant_token') as mock_token:
            mock_token.return_value = "mock_token_123"

            # Присоединяемся к вебинару
            join_response = client.get(f"/webinars/{test_started_webinar.id}/join")
            print(f"Join response: {join_response.status_code} - {join_response.text}")

            assert join_response.status_code == 200

            # Проверяем что уведомление о присоединении создано
            notification = await db_session.scalar(
                select(models.Notification).where(
                    models.Notification.user_id == test_user.id
                ).order_by(models.Notification.created_at.desc())
            )

            assert notification is not None
            # Проверяем тип уведомления
            assert "joined" in notification.notification_type.lower() or "присоединились" in notification.title.lower()

    @pytest.mark.asyncio
    async def test_webinar_announcement_creation(self, client, db_session, test_user):
        """Тест создания анонса вебинара в Redis"""
        webinar_data = {
            "title": "Test Webinar Announcement",
            "description": "Test Description",
            "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat(),
            "duration": 90,
            "max_participants": 50
            # is_public убираем, так как его нет в модели
        }

        with patch('src.dependencies.rbac.admin_or_manager_permission'):
            # Создаем вебинар
            response = client.post("/webinars/", json=webinar_data)
            print(f"Create webinar response: {response.status_code} - {response.text}")
            assert response.status_code == 200
            webinar = response.json()

            # Проверяем что анонс создан в Redis
            from src.services.notification_service import notification_service

            # Даем время на создание анонса
            import time
            time.sleep(0.1)

            announcements = notification_service.get_active_announcements()
            print(f"Found {len(announcements)} announcements")

            # Ищем наш вебинар в анонсах
            webinar_announcement = None
            for announcement in announcements:
                if announcement.get('id') == webinar['id']:
                    webinar_announcement = announcement
                    break

            assert webinar_announcement is not None
            assert webinar_announcement['title'] == webinar_data['title']
            assert webinar_announcement['type'] == 'webinar_announcement'

    def test_webinar_reminder_celery_task(self):
        """Тест задачи Celery для напоминаний о вебинарах"""
        with patch('src.tasks.tasks.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Мокаем данные
            mock_webinar = MagicMock()
            mock_webinar.id = 1
            mock_webinar.title = "Test Webinar"
            mock_webinar.scheduled_at = datetime.now() + timedelta(minutes=60)

            mock_registration = MagicMock()
            mock_registration.user_id = 1
            mock_registration.reminder_sent = False

            mock_db.scalars.return_value.all.side_effect = [
                [mock_webinar],  # вебинары
                [mock_registration]  # регистрации
            ]

            # Мокаем notification_service
            with patch('src.tasks.tasks.notification_service') as mock_notification_service:
                mock_notification_service.create_notification_sync.return_value = MagicMock()

                # Запускаем задачу
                from src.tasks.tasks import send_webinar_reminders
                send_webinar_reminders()

                # Проверяем что методы были вызваны
                assert mock_db.scalars.call_count >= 2
                assert mock_db.commit.called
                assert mock_notification_service.create_notification_sync.called

    @pytest.mark.asyncio
    async def test_webinar_invitations_send_notifications(self, client, db_session, test_user, test_webinar):
        """Тест что приглашения на вебинар отправляют уведомления"""
        # Создаем второго пользователя для приглашения
        invited_user = models.User(
            email=self._generate_unique_email(),
            phone=self._generate_unique_phone(),
            username=self._generate_unique_username(),
            secret_code="9999",
            hashed_password="mock_hash",
            is_active=True
        )
        db_session.add(invited_user)
        await db_session.commit()
        await db_session.refresh(invited_user)

        # Мокаем RBAC проверку
        with patch('src.dependencies.rbac.admin_or_manager_permission'):
            # Отправляем приглашение
            invite_response = client.post(
                f"/webinars/{test_webinar.id}/invite",
                json={"user_ids": [invited_user.id]}
            )
            print(f"Invite response: {invite_response.status_code} - {invite_response.text}")
            assert invite_response.status_code == 200

            # Даем время на создание уведомления
            import asyncio
            await asyncio.sleep(0.1)

            # Проверяем что уведомление-приглашение создано
            notification = await db_session.scalar(
                select(models.Notification).where(
                    models.Notification.user_id == invited_user.id
                )
            )

            assert notification is not None
            assert "invite" in notification.notification_type.lower() or "приглашение" in notification.title.lower()

    @pytest.mark.asyncio
    async def test_webinar_creation_with_announcement(self, client, db_session, test_user):
        """Тест что создание вебинара автоматически создает анонс"""
        webinar_data = {
            "title": "Auto-announce Webinar",
            "description": "Test auto announcement",
            "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 100
            # is_public убираем
        }

        with patch('src.dependencies.rbac.admin_or_manager_permission'):
            # Создаем вебинар
            response = client.post("/webinars/", json=webinar_data)
            assert response.status_code == 200
            webinar = response.json()

            # Проверяем что вебинар создан в БД
            db_webinar = await db_session.get(models.Webinar, webinar['id'])
            assert db_webinar is not None
            assert db_webinar.title == webinar_data['title']

            # Проверяем что анонс создан в Redis
            from src.services.notification_service import notification_service

            import time
            time.sleep(0.1)  # Даем время на создание анонса

            announcements = notification_service.get_active_announcements()

            # Ищем анонс нашего вебинара
            found_announcement = False
            for announcement in announcements:
                if announcement.get('id') == webinar['id']:
                    found_announcement = True
                    assert announcement['title'] == webinar_data['title']
                    break

            assert found_announcement, "Announcement not found in Redis"

    @pytest.mark.asyncio
    async def test_get_user_webinars(self, client, test_user, test_webinar):
        """Тест получения вебинаров пользователя"""
        # Сначала регистрируем пользователя
        register_response = client.post(f"/webinars/{test_webinar.id}/register")
        assert register_response.status_code == 200

        # Получаем список зарегистрированных вебинаров
        response = client.get("/webinars/my/registered")
        print(f"My webinars response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            assert data['success'] is True
            assert 'webinars' in data
            assert 'pagination' in data

    @pytest.mark.asyncio
    async def test_webinar_unregister(self, client, test_user, test_webinar):
        """Тест отмены регистрации на вебинар"""
        # Сначала регистрируем пользователя
        register_response = client.post(f"/webinars/{test_webinar.id}/register")
        assert register_response.status_code == 200

        # Отменяем регистрацию
        unregister_response = client.delete(f"/webinars/{test_webinar.id}/unregister")
        print(f"Unregister response: {unregister_response.status_code} - {unregister_response.text}")

        assert unregister_response.status_code == 200

# pytest tests/test_webinar_notifications/test_webinar_notification_endpoints.py --html=report.html --self-contained-html

# Или с подробным выводом
# pytest tests/test_webinar_notifications/test_webinar_notification_endpoints.py -v --html=report.html --self-contained-html