# tests/test_auth_diagnostic.py
import pytest
from fastapi.testclient import TestClient

def test_auth_endpoints_availability(client: TestClient):
    """Диагностика доступности эндпоинтов аутентификации"""
    print("\n🔍 Диагностика эндпоинтов аутентификации:")

    endpoints = [
        ("GET", "/auth/"),  # Проверим базовый путь
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("POST", "/auth/verify-2fa"),
        ("GET", "/auth/me"),
        ("GET", "/auth/protected-data"),
        ("POST", "/auth/resend-sms"),
        ("POST", "/auth/logout"),
    ]

    for method, path in endpoints:
        try:
            if method == "GET":
                response = client.get(path)
            else:
                # Для POST отправляем минимальные данные
                json_data = {}
                if path == "/auth/register":
                    json_data = {
                        "email": "test@example.com",
                        "phone": "+79001234567",
                        "username": "testuser",
                        "secret_code": "1234",
                        "password": "testpass123"
                    }
                elif path == "/auth/login":
                    json_data = {"email": "test@example.com", "secret_code": "1234"}
                elif path == "/auth/verify-2fa":
                    json_data = {"user_id": 1, "sms_code": "123456"}
                elif path == "/auth/resend-sms":
                    json_data = {"user_id": 1}

                response = client.post(path, json=json_data) if json_data else client.post(path)

            print(f"  {method} {path} -> {response.status_code}")

            # Анализируем ответы
            if response.status_code == 404:
                print(f"    ❌ ЭНДПОИНТ НЕ НАЙДЕН!")
            elif response.status_code == 422:
                print(f"    ⚠️  Ошибка валидации (ожидаемо для теста)")
            elif response.status_code == 500:
                print(f"    🔥 Internal Server Error: {response.text}")

        except Exception as e:
            print(f"    💥 Исключение при запросе: {e}")


def test_main_endpoints_availability(client: TestClient):
    """Диагностика основных эндпоинтов"""
    print("\n🔍 Диагностика основных эндпоинтов:")

    endpoints = [
        ("GET", "/"),
        ("GET", "/dashboard"),
        ("GET", "/register"),
        ("GET", "/login"),
        ("GET", "/api/health"),
        ("GET", "/api/root"),
        ("GET", "/api/status"),
    ]

    for method, path in endpoints:
        response = client.get(path)
        print(f"  {method} {path} -> {response.status_code}")

        if response.status_code == 404:
            print(f"    ❌ ЭНДПОИНТ НЕ НАЙДЕН!")
        elif response.status_code >= 500:
            print(f"    🔥 Server Error: {response.text}")


def test_webinar_endpoints_availability(client: TestClient):
    """Диагностика эндпоинтов вебинаров"""
    print("\n🔍 Диагностика эндпоинтов вебинаров:")

    endpoints = [
        ("GET", "/webinars/"),
        ("POST", "/webinars/"),
        ("GET", "/webinars/1"),
        ("PUT", "/webinars/1"),
        ("DELETE", "/webinars/1"),
        ("POST", "/webinars/1/register"),
        ("POST", "/webinars/1/cancel-registration"),
    ]

    for method, path in endpoints:
        try:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path, json={})
            elif method == "PUT":
                response = client.put(path, json={})
            elif method == "DELETE":
                response = client.delete(path)

            print(f"  {method} {path} -> {response.status_code}")

            if response.status_code == 404:
                print(f"    ❌ ЭНДПОИНТ НЕ НАЙДЕН!")

        except Exception as e:
            print(f"    💥 Исключение: {e}")

# pytest tests/tests_auth/test_auth_diagnostic.py --html=report.html