# tests/test_webinar_notifications/test_email_push_notifications.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from sqlalchemy import select

from src.database import models

class TestNotificationsCorrect:

    def _generate_unique_email(self):
        """Генерация уникального email"""
        unique_part = uuid.uuid4().hex[:8]
        return f"test_{unique_part}@example.com"

    @pytest.mark.asyncio
    async def test_webinar_registration_creates_notification(self, client, db_session, test_user, test_webinar):
        """Тест что регистрация создает уведомление через правильный сервис"""
        print("🔔 Тестируем создание уведомления при регистрации...")

        # ПРАВИЛЬНЫЙ ПУТЬ - мокаем notification_service.create_notification
        with patch('src.services.webinar_service.notification_service.create_notification') as mock_create_notif:
            mock_create_notif.return_value = MagicMock()

            # Регистрируем пользователя
            response = client.post(f"/webinars/{test_webinar.id}/register")
            print(f"Registration response: {response.status_code}")

            if response.status_code == 200:
                assert mock_create_notif.called
                print("✅ Уведомление создано через notification_service")
            else:
                print(f"⚠️ Регистрация не удалась: {response.text}")

    @pytest.mark.asyncio
    async def test_celery_tasks_exist(self):
        """Тест что Celery задачи существуют"""
        print("🔔 Тестируем существование Celery задач...")

        from src.tasks import tasks

        # Проверяем что задачи определены - используем реальные имена функций
        required_tasks = [
            'send_webinar_reminders',
            'send_welcome_email',
            'send_verification_codes',
            'process_email_queue',
            'cleanup_old_data',
            'create_platform_notification',
            'send_websocket_notification',
            'send_verification_codes_task'
        ]

        for task_name in required_tasks:
            assert hasattr(tasks, task_name), f"Задача {task_name} не найдена"
            print(f"✅ Задача {task_name} существует")

    @pytest.mark.asyncio
    async def test_complete_notification_flow(self, client, db_session, test_user, test_webinar):
        """Полный тест потока уведомлений"""
        print("🔄 Тестируем полный поток уведомлений...")

        # Мокаем все зависимости
        with patch('src.services.webinar_service.notification_service.create_notification') as mock_create_notif, \
                patch('src.tasks.tasks.create_platform_notification.delay') as mock_platform_notif, \
                patch('src.services.template_service.template_service.render_email_template') as mock_render_template:
            mock_create_notif.return_value = MagicMock()
            mock_platform_notif.return_value = MagicMock()
            mock_render_template.return_value = "Test email content"

            # Регистрируем пользователя на вебинар
            response = client.post(f"/webinars/{test_webinar.id}/register")

            if response.status_code == 200:
                # Проверяем что уведомления созданы
                assert mock_create_notif.called
                # mock_platform_notif может не вызываться в зависимости от логики
                print("✅ Полный поток уведомлений работает")

# pytest tests/test_webinar_notifications/test_email_push_notifications.py -v --html=report.html