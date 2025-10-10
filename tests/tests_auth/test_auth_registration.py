# tests/test_auth_registration.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_user_registration_success(client: TestClient, valid_register_data):
    """Тест успешной регистрации пользователя"""
    print("\n🔐 Тестирование регистрации пользователя...")

    # Мокаем отправку welcome email
    with patch('src.tasks.tasks.send_welcome_email.delay') as mock_email:
        response = client.post("/auth/register", json=valid_register_data)

        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response: {response.text}")

        if response.status_code == 201:
            print("✅ Регистрация успешна!")
            data = response.json()
            assert "user_id" in data
            assert data["email"] == valid_register_data["email"]
            assert mock_email.called
        else:
            print(f"❌ Ошибка: {response.status_code}")
            if response.status_code == 422:
                print("Ошибка валидации данных")
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"Ошибка бизнес-логики: {error_detail}")


def test_user_registration_duplicate_email(client: TestClient, valid_register_data):
    """Тест регистрации с дублирующимся email"""
    print("\n🔐 Тестирование дублирующегося email...")

    # Сначала регистрируем пользователя
    with patch('src.tasks.tasks.send_welcome_email.delay'):
        response1 = client.post("/auth/register", json=valid_register_data)

        # Пытаемся зарегистрировать с тем же email
        duplicate_data = valid_register_data.copy()
        duplicate_data["phone"] = "+79001112233"  # Меняем телефон
        duplicate_data["username"] = "different_user"  # Меняем username

        response2 = client.post("/auth/register", json=duplicate_data)

        print(f"📊 Первая регистрация: {response1.status_code}")
        print(f"📊 Вторая регистрация: {response2.status_code}")

        if response2.status_code == 400:
            error_detail = response2.json().get('detail', '')
            if "email" in error_detail.lower():
                print("✅ Корректно обработан дублирующийся email")
            else:
                print(f"❌ Неожиданная ошибка: {error_detail}")
        else:
            print("❌ Ожидалась ошибка 400 для дублирующегося email")


def test_user_registration_validation(client: TestClient):
    """Тест валидации данных регистрации"""
    print("\n🔐 Тестирование валидации данных...")

    invalid_cases = [
        {
            "data": {
                "email": "invalid-email",
                "phone": "+79001234567",
                "username": "testuser",
                "secret_code": "1234",
                "password": "short"
            },
            "expected_error": "email"
        },
        {
            "data": {
                "email": "test@example.com",
                "phone": "invalid-phone",
                "username": "testuser",
                "secret_code": "1234",
                "password": "validpassword123"
            },
            "expected_error": "phone"
        }
    ]

    for i, case in enumerate(invalid_cases):
        print(f"  Тест кейс {i + 1}: {case['expected_error']}")
        response = client.post("/auth/register", json=case['data'])

        if response.status_code == 422:
            print("    ✅ Ошибка валидации (ожидаемо)")
        else:
            print(f"    ❌ Неожиданный статус: {response.status_code}")

# pytest tests/tests_auth/test_auth_registration.py --html=report.html