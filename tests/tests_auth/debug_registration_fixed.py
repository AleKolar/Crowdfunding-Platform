# tests/tests_auth/debug_registration_fixed.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy import select


@pytest.mark.asyncio
async def test_debug_webinar_registration(client, db_session, test_user, test_webinar):
    """Диагностика теста регистрации на вебинар"""
    print("🔍 Диагностика теста регистрации...")

    # Проверяем что фикстуры работают
    print(f"👤 Тестовый пользователь: {test_user.id} - {test_user.email}")
    print(f"🎯 Тестовый вебинар: {test_webinar.id} - {test_webinar.title}")
    print(f"📊 Статус вебинара: {test_webinar.status}")
    print(f"📊 Доступные слоты: {test_webinar.max_participants}")  # Используем прямое поле вместо свойства

    # Проверяем что таблицы существуют
    from sqlalchemy import text
    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    users_table = result.scalar_one_or_none()
    print(f"📋 Таблица users существует: {users_table is not None}")

    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='webinars'"))
    webinars_table = result.scalar_one_or_none()
    print(f"📋 Таблица webinars существует: {webinars_table is not None}")

    # ПРАВИЛЬНЫЙ ПУТЬ ДЛЯ МОКА - патчим импорт в webinar_service
    with patch('src.services.webinar_service.notification_service') as mock_notif_service:
        # Создаем мок для notification_service
        mock_notif_instance = MagicMock()
        mock_notif_instance.create_notification.return_value = MagicMock()
        mock_notif_service.return_value = mock_notif_instance

        # Тестируем регистрацию
        print(f"\n🚀 Тестируем регистрацию на вебинар {test_webinar.id}...")
        response = client.post(f"/webinars/{test_webinar.id}/register")

        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response body: {response.text}")

        if response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Ошибка: {error_detail}")

            # Проверяем состояние после ошибки
            await db_session.refresh(test_webinar)
            print(f"📊 Вебинар после ошибки - статус: {test_webinar.status}")

            # Проверяем существующие регистрации
            from src.database.models import WebinarRegistration
            existing_reg = await db_session.scalar(
                select(WebinarRegistration).where(
                    WebinarRegistration.webinar_id == test_webinar.id,
                    WebinarRegistration.user_id == test_user.id
                )
            )
            print(f"📊 Существующая регистрация: {existing_reg}")

        elif response.status_code == 200:
            print("✅ Регистрация успешна!")

            # Проверяем что регистрация создалась
            from src.database.models import WebinarRegistration
            registration = await db_session.scalar(
                select(WebinarRegistration).where(
                    WebinarRegistration.webinar_id == test_webinar.id,
                    WebinarRegistration.user_id == test_user.id
                )
            )
            print(f"📊 Созданная регистрация: {registration}")

            # Проверяем что уведомление было вызвано
            assert mock_notif_instance.create_notification.called
            print("✅ Уведомление отправлено")

# pytest tests/tests_auth/debug_registration_fixed.py --html=report.html --self-contained-html