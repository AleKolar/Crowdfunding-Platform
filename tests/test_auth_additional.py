# tests/test_auth_additional.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def test_resend_sms_success(client: TestClient, test_user, mock_verification_codes):
    """Тест повторной отправки SMS и Email"""
    response = client.post("/auth/resend-code", json={"email": test_user.email})

    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Новые коды подтверждения отправлены по SMS и Email"
    assert data["test_sms_code"] == "123456"
    assert data["test_email_code"] == "123456"
    assert data["sms_sent"] is True
    assert data["email_sent"] is True
    assert data["user_phone"] == test_user.phone
    assert data["user_email"] == test_user.email
    assert mock_verification_codes.called


def test_resend_sms_debug_mock(client: TestClient, test_user):
    """Диагностика мока generate_and_send_verification_codes"""

    test_paths = [
        'src.security.auth.generate_and_send_verification_codes',
        'src.endpoints.auth.generate_and_send_verification_codes',
    ]

    for path in test_paths:
        with patch(path, new_callable=AsyncMock) as mock:
            mock.return_value = {
                "sms_code": "999999",
                "email_code": "999999",
                "code": "999999",
                "sms_sent": True,
                "email_sent": True
            }

            response = client.post("/auth/resend-code", json={"email": test_user.email})
            assert response.status_code == 200

            data = response.json()
            if data["test_sms_code"] != "999999":
                continue

            assert data["test_email_code"] == "999999"
            assert data["sms_sent"] is True
            assert data["email_sent"] is True
            assert mock.called
            return

    pytest.fail("Ни один путь мока generate_and_send_verification_codes не сработал")


def test_resend_sms_with_endpoint_mock(client: TestClient, test_user):
    """Мокаем generate_and_send_verification_codes в endpoints/auth.py"""

    with patch('src.endpoints.auth.generate_and_send_verification_codes', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sms_code": "123456",
            "email_code": "123456",
            "code": "123456",
            "sms_sent": True,
            "email_sent": True
        }

        response = client.post("/auth/resend-code", json={"email": test_user.email})

        assert response.status_code == 200

        data = response.json()
        assert data["test_sms_code"] == "123456"
        assert data["test_email_code"] == "123456"
        assert data["sms_sent"] is True
        assert data["email_sent"] is True
        assert mock.called


def test_resend_sms_simple(client: TestClient, test_user):
    """Простой тест без мока - проверяем, что эндпоинт работает"""

    response = client.post("/auth/resend-code", json={"email": test_user.email})

    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "test_sms_code" in data
    assert "test_email_code" in data
    assert "user_phone" in data
    assert "user_email" in data


def test_logout_success(client: TestClient):
    """Тест выхода из системы"""

    response = client.post("/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_get_me_with_overridden_user(client: TestClient):
    """Тест получения профиля пользователя через зависимость override"""

    response = client.get("/auth/me")
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == 1
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


def test_validation_errors(client: TestClient):
    """Тест валидации входных данных"""

    invalid_cases = [
        {"data": {"email": "invalid-email", "secret_code": "1234"}, "description": "Невалидный email"},
        {"data": {"email": "test@example.com", "secret_code": "123"}, "description": "Секретный код < 4 цифр"},
        {"data": {"email": "test@example.com", "secret_code": "12345"}, "description": "Секретный код > 4 цифр"},
        {"data": {"email": "test@example.com", "secret_code": "12a4"}, "description": "Секретный код с буквами"},
    ]

    for case in invalid_cases:
        response = client.post("/auth/login", json=case["data"])
        assert response.status_code == 422
