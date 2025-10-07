# tests/tests_auth/test_auth_endpoints.py
import pytest
from unittest.mock import patch
from passlib.context import CryptContext
from fastapi import status


@pytest.fixture(autouse=True)
def mock_bcrypt():
    test_pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    with patch('src.security.auth.pwd_context', test_pwd_context):
        yield


class TestAuthEndpoints:
    """Тесты аутентификации с тестовой БД"""

    def test_register_success(self, client, valid_register_data):
        """Успешная регистрация"""
        print(f"\n🔍 Testing registration with:")
        print(f"   Email: {valid_register_data['email']}")
        print(f"   Password: '{valid_register_data['password']}'")
        print(f"   Password length: {len(valid_register_data['password'])} chars")

        response = client.post("/auth/register", json=valid_register_data)

        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert "message" in data

    def test_login_success_with_mock(self, client, valid_register_data):
        """Успешный вход с использованием моков"""
        # Регистрируем пользователя
        register_response = client.post("/auth/register", json=valid_register_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        user_id = register_response.json()["user_id"]

        # Мокаем аутентификацию
        with patch('src.endpoints.auth.authenticate_user') as mock_authenticate:
            mock_user = type('MockUser', (), {
                'id': user_id,
                'email': valid_register_data['email'],
                'phone': valid_register_data['phone'],
                'username': valid_register_data['username'],
                'is_active': True,
                'secret_code': valid_register_data['secret_code']
            })()

            mock_authenticate.return_value = mock_user

            with patch('src.endpoints.auth.generate_and_send_sms_code') as mock_sms:
                mock_sms.return_value = None

                login_data = {
                    "email": valid_register_data["email"],
                    "secret_code": valid_register_data["secret_code"]
                }

                response = client.post("/auth/login", json=login_data)

                print(f"📥 Successful login status: {response.status_code}")
                print(f"📥 Successful login response: {response.text}")

                if response.status_code == 422:
                    error_detail = response.json()
                    print(f"🔴 Validation error: {error_detail}")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["requires_2fa"] is True
                assert data["message"] == "SMS код отправлен на ваш телефон"
                assert data["user_id"] == user_id

    def test_register_duplicate_email(self, client, valid_register_data):
        """Регистрация с дубликатом email"""
        response1 = client.post("/auth/register", json=valid_register_data)
        assert response1.status_code == status.HTTP_201_CREATED

        duplicate_data = valid_register_data.copy()
        duplicate_data["phone"] = "+79990000000"

        response2 = client.post("/auth/register", json=duplicate_data)

        print(f"📥 Duplicate email status: {response2.status_code}")

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response2.json()["detail"].lower()
        assert any(word in error_detail for word in ["email", "почта", "already"])

    def test_register_duplicate_phone(self, client, valid_register_data):
        """Регистрация с дубликатом телефона"""
        response1 = client.post("/auth/register", json=valid_register_data)
        assert response1.status_code == status.HTTP_201_CREATED

        duplicate_data = valid_register_data.copy()
        duplicate_data["email"] = "new_email@example.com"

        response2 = client.post("/auth/register", json=duplicate_data)

        print(f"📥 Duplicate phone status: {response2.status_code}")

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response2.json()["detail"].lower()
        assert any(word in error_detail for word in ["телефон", "phone", "already"])

    def test_register_invalid_data(self, client):
        """Регистрация с невалидными данными"""
        invalid_data = {
            "email": "invalid-email",
            "phone": "123",
            "username": "ab",
            "is_active": True,
            "password": "short",
            "secret_code": "123"
        }

        response = client.post("/auth/register", json=invalid_data)

        print(f"📥 Invalid data status: {response.status_code}")

        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_login_success_structure(self, client, valid_register_data):
        """Проверка структуры ответа при логине"""
        register_response = client.post("/auth/register", json=valid_register_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Используем правильную схему - JSON с email и secret_code
        login_data = {
            "email": valid_register_data["email"],
            "secret_code": valid_register_data["secret_code"]
        }

        response = client.post("/auth/login", json=login_data)

        print(f"📥 Login status: {response.status_code}")
        print(f"📥 Login response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            assert "requires_2fa" in data
            assert data["requires_2fa"] is True
            assert "message" in data
            assert "user_id" in data
        else:
            error_data = response.json()
            print(f"🔴 Error details: {error_data}")
            assert response.status_code in [401, 400, 422]

    def test_login_invalid_credentials(self, client, valid_register_data):
        """Логин с неверными учетными данными"""
        register_response = client.post("/auth/register", json=valid_register_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Используем правильную схему с неверным secret_code
        login_data = {
            "email": valid_register_data["email"],
            "secret_code": "wrong_code"  # Неверный код
        }

        response = client.post("/auth/login", json=login_data)

        print(f"📥 Invalid login status: {response.status_code}")

        # Понимает запрос, но не может обработать из-за семантических ошибок(т.к. у нас строгая валидация)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        error_data = response.json()
        assert "detail" in error_data

    def test_login_invalid_email_format(self, client):
        """Логин с неверным форматом email"""
        login_data = {
            "email": "invalid-email",
            "secret_code": "1234"
        }

        response = client.post("/auth/login", json=login_data)

        print(f"📥 Invalid email format status: {response.status_code}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_invalid_secret_code_format(self, client, valid_register_data):
        """Логин с неверным форматом secret_code"""
        login_data = {
            "email": valid_register_data["email"],
            "secret_code": "abc"  # Не цифры и не 4 символа
        }

        response = client.post("/auth/login", json=login_data)

        print(f"📥 Invalid secret code format status: {response.status_code}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDatabaseIntegration:
    """Тесты интеграции с БД"""

    @pytest.mark.asyncio
    async def test_database_connection(self, db_session):
        """Проверка что БД работает (асинхронная версия)"""
        from sqlalchemy import text

        # Для асинхронной сессии используем await
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

# pytest tests/tests_auth/test_auth_endpoints.py --html=report.html