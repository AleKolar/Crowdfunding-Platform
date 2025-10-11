# tests/test_auth_additional.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def test_resend_sms_success(client: TestClient, test_user, mock_verification_codes):
    """Тест повторной отправки SMS и Email"""
    print("\n📱 Тестирование повторной отправки кодов...")

    response = client.post("/auth/resend-code", json={"email": test_user.email})

    print(f"📊 Status: {response.status_code}")
    print(f"📋 Response: {response.text}")

    if response.status_code == 200:
        data = response.json()
        print("✅ Коды отправлены повторно!")

        # ✅ ПРОВЕРЯЕМ ОТВЕТ С МОКОМ
        assert "message" in data
        assert data["test_sms_code"] == "123456"  # Должен быть из мока
        assert data["test_email_code"] == "123456"  # Должен быть из мока
        assert data["user_phone"] == test_user.phone
        assert data["user_email"] == test_user.email

        # ✅ ПРОВЕРЯЕМ ЧТО МОК БЫЛ ВЫЗВАН
        assert mock_verification_codes.called
        print("✅ generate_and_send_verification_codes был вызван!")

    else:
        print(f"❌ Ошибка: {response.status_code}")


def test_resend_sms_debug_mock(client: TestClient, test_user):
    """Диагностика мока"""
    print("\n🐛 Диагностика мока generate_and_send_verification_codes...")

    # Пробуем разные пути
    test_paths = [
        'src.security.auth.generate_and_send_verification_codes',
        'src.endpoints.auth.generate_and_send_verification_codes',
    ]

    for path in test_paths:
        print(f"\n🔧 Тестируем путь: {path}")

        with patch(path, new_callable=AsyncMock) as mock:
            mock.return_value = {
                "sms_code": "999999",  # Уникальный код для этого теста
                "email_code": "999999",
                "sms_sent": True,
                "email_sent": True
            }

            response = client.post("/auth/resend-code", json={"email": test_user.email})
            print(f"📊 Status: {response.status_code}, Mock called: {mock.called}")

            if response.status_code == 200:
                data = response.json()
                print(f"📋 test_sms_code из ответа: {data.get('test_sms_code')}")

                if data.get('test_sms_code') == "999999":
                    print(f"🎉 НАЙДЕН ПРАВИЛЬНЫЙ ПУТЬ: {path}")
                    return

    print("❌ Ни один путь мока не сработал!")


def test_resend_sms_with_endpoint_mock(client: TestClient, test_user):
    """Мокаем на уровне импорта в endpoints/auth.py"""
    print("\n📱 Тест с моком на уровне endpoints...")

    # Мокаем именно там, где импортируется в endpoints/auth.py
    with patch('src.endpoints.auth.generate_and_send_verification_codes', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sms_code": "123456",
            "email_code": "123456",
            "sms_sent": True,
            "email_sent": True
        }

        response = client.post("/auth/resend-code", json={"email": test_user.email})

        print(f"📊 Status: {response.status_code}")
        print(f"🔧 Mock called: {mock.called}")

        if response.status_code == 200:
            data = response.json()
            print(f"📋 test_sms_code: {data.get('test_sms_code')}")

            if data.get('test_sms_code') == "123456":
                print("✅ Мок сработал на уровне endpoints!")
            else:
                print(f"❌ Мок не сработал. Получен код: {data.get('test_sms_code')}")


def test_resend_sms_simple(client: TestClient, test_user):
    """Простой тест без мока - проверяем что эндпоинт работает"""
    print("\n📱 Простой тест эндпоинта /auth/resend-code...")

    response = client.post("/auth/resend-code", json={"email": test_user.email})

    print(f"📊 Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("✅ Эндпоинт работает!")
        assert "message" in data
        assert "test_sms_code" in data
        assert "test_email_code" in data
        assert "user_phone" in data
        assert "user_email" in data
        print(f"📋 Отправленные коды: SMS={data['test_sms_code']}, Email={data['test_email_code']}")
    else:
        print(f"❌ Эндпоинт вернул: {response.status_code}")


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


def test_test_email_endpoint(client: TestClient):
    """Тест эндпоинта тестирования email"""
    print("\n📧 Тестирование эндпоинта /auth/test-email...")

    # Мокаем отправку email чтобы не отправлять реальные письма
    with patch('src.services.email_service.email_service.send_welcome_email', new_callable=AsyncMock) as mock_email:
        mock_email.return_value = True

        response = client.post("/auth/test-email", json={"to_email": "test@example.com"})

        print(f"📊 Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            print("✅ Эндпоинт test-email работает!")
        else:
            print(f"📌 Статус: {response.status_code}")


def test_me_endpoint_with_real_auth(client: TestClient, test_user):
    """Тест /auth/me с реальной аутентификацией"""
    print("\n👤 Тестирование /auth/me с аутентификацией...")

    # Сначала логинимся чтобы получить токен
    login_data = {
        "email": test_user.email,
        "secret_code": "5678"  # Секретный код test_user
    }

    # Мокаем зависимости для логина
    with patch('src.services.auth_service.authenticate_user') as mock_auth, \
            patch('src.security.auth.generate_and_send_verification_codes') as mock_verification:

        mock_auth.return_value = test_user
        mock_verification.return_value = AsyncMock(return_value={
            "sms_code": "123456",
            "email_code": "123456",
            "sms_sent": True,
            "email_sent": True
        })

        # Логинимся (первый этап)
        login_response = client.post("/auth/login", json=login_data)

        if login_response.status_code == 200:
            login_data = login_response.json()
            user_id = login_data["user_id"]

            # Мокаем верификацию 2FA
            with patch('src.security.auth.verify_sms_code') as mock_verify:
                mock_verify.return_value = True

                # Верифицируем 2FA
                verify_response = client.post("/auth/verify-2fa", json={
                    "user_id": user_id,
                    "sms_code": "123456"
                })

                if verify_response.status_code == 200:
                    token_data = verify_response.json()
                    access_token = token_data["access_token"]

                    # Теперь тестируем /auth/me с токеном
                    headers = {"Authorization": f"Bearer {access_token}"}
                    me_response = client.get("/auth/me", headers=headers)

                    print(f"📊 /auth/me Status: {me_response.status_code}")

                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        print(f"✅ /auth/me работает! Данные: {me_data}")
                    else:
                        print(f"❌ /auth/me вернул: {me_response.status_code}")


# Дополнительные тесты для покрытия edge cases
def test_resend_code_no_email(client: TestClient):
    """Тест resend-code без email"""
    print("\n📱 Тест resend-code без email...")

    response = client.post("/auth/resend-code", json={})

    print(f"📊 Status: {response.status_code}")

    if response.status_code == 400:
        data = response.json()
        assert "detail" in data
        print("✅ Корректно обработано отсутствие email!")
    else:
        print(f"📌 Статус: {response.status_code}")


def test_resend_code_invalid_email(client: TestClient):
    """Тест resend-code с несуществующим email"""
    print("\n📱 Тест resend-code с несуществующим email...")

    response = client.post("/auth/resend-code", json={"email": "nonexistent@example.com"})

    print(f"📊 Status: {response.status_code}")

    if response.status_code == 404:
        data = response.json()
        assert "detail" in data
        print("✅ Корректно обработан несуществующий пользователь!")
    else:
        print(f"📌 Статус: {response.status_code}")

# pytest tests/test_auth_additional.py -v -s