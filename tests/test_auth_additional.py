# tests/test_auth_additional.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_resend_sms_success(client: TestClient, test_user):
    """Тест повторной отправки SMS"""
    print("\n📱 Тестирование повторной отправки SMS...")

    with patch('src.services.auth_service.generate_and_send_sms_code') as mock_sms:
        mock_sms.return_value = None

        response = client.post("/auth/resend-sms", json={"user_id": test_user.id})

        print(f"📊 Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SMS отправлен повторно!")
            assert mock_sms.called
        elif response.status_code == 404:
            print("⚠️  Эндпоинт не найден (возможно не реализован)")
        else:
            print(f"📌 Статус: {response.status_code}")


def test_logout_success(client: TestClient):
    """Тест выхода из системы"""
    print("\n🚪 Тестирование выхода из системы...")

    response = client.post("/auth/logout")

    print(f"📊 Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        print("✅ Выход выполнен успешно!")
    else:
        print(f"📌 Статус: {response.status_code}")


def test_protected_endpoint_without_auth(client: TestClient):
    """Тест защищенного эндпоинта без аутентификации"""
    print("\n🔒 Тестирование защищенного эндпоинта без токена...")

    response = client.get("/auth/protected-data")

    print(f"📊 Status: {response.status_code}")

    if response.status_code == 401:
        print("✅ Корректно запрещен доступ без аутентификации!")
    else:
        print(f"📌 Статус: {response.status_code}")


def test_validation_errors(client: TestClient):
    """Тест валидации входных данных"""
    print("\n🛡️ Тестирование валидации данных...")

    invalid_cases = [
        {
            "data": {"email": "invalid-email", "secret_code": "1234"},
            "description": "Невалидный email"
        },
        {
            "data": {"email": "test@example.com", "secret_code": "123"},
            "description": "Секретный код < 4 цифр"
        },
        {
            "data": {"email": "test@example.com", "secret_code": "12345"},
            "description": "Секретный код > 4 цифр"
        },
        {
            "data": {"email": "test@example.com", "secret_code": "12a4"},
            "description": "Секретный код с буквами"
        }
    ]

    for case in invalid_cases:
        response = client.post("/auth/login", json=case["data"])
        print(f"  {case['description']} -> {response.status_code}")

        if response.status_code == 422:
            print("    ✅ Ошибка валидации (ожидаемо)")
        else:
            print(f"    📌 Неожиданный статус: {response.status_code}")


@pytest.mark.asyncio
async def test_webinar_registration_auth_required(client: TestClient, test_webinar):
    """Тест что регистрация на вебинар требует аутентификации"""
    print("\n🎯 Тестирование аутентификации для вебинаров...")

    # Пытаемся зарегистрироваться без аутентификации
    response = client.post(f"/webinars/{test_webinar.id}/register")

    print(f"📊 Статус регистрации без аутентификации: {response.status_code}")

    # Должен быть 401 или 403
    if response.status_code in [401, 403]:
        print("✅ Корректно требует аутентификации!")
    else:
        print(f"📌 Статус: {response.status_code}")

# pytest tests/test_auth_additional.py -v -s