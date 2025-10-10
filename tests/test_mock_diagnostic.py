# tests/test_mock_diagnostic.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


def test_find_correct_mock_path(client: TestClient, test_user):
    """Тест для определения правильного пути мока"""
    print("\n🔍 Поиск правильного пути для мока...")

    login_data = {
        "email": test_user.email,
        "secret_code": "5678"
    }

    # Пробуем разные пути
    mock_paths = [
        'src.endpoints.auth.authenticate_user',
        'src.security.auth.authenticate_user',
        'src.services.auth_service.authenticate_user',
        'main.authenticate_user',
    ]

    for mock_path in mock_paths:
        print(f"\n🔧 Пробуем мок: {mock_path}")

        try:
            with patch(mock_path) as mock_auth:
                mock_auth.return_value = test_user

                response = client.post("/auth/login", json=login_data)
                print(f"   Status: {response.status_code}")
                print(f"   Mock called: {mock_auth.called}")

                if mock_auth.called:
                    print(f"   ✅ НАЙДЕН ПРАВИЛЬНЫЙ ПУТЬ: {mock_path}")
                    break
                else:
                    print(f"   ❌ Мок не вызвался")

        except Exception as e:
            print(f"   💥 Ошибка: {e}")


def test_trace_imports():
    """Трассировка импортов для понимания структуры"""
    print("\n🔍 Трассировка импортов...")

    try:
        from src.endpoints import auth as endpoints_auth
        print("✅ src.endpoints.auth импортирован")
        if hasattr(endpoints_auth, 'authenticate_user'):
            print("   📍 authenticate_user найден в endpoints.auth")
        else:
            print("   ❌ authenticate_user НЕ найден в endpoints.auth")
    except ImportError as e:
        print(f"❌ Не удалось импортировать endpoints.auth: {e}")

    try:
        from src.security import auth as security_auth
        print("✅ src.security.auth импортирован")
        if hasattr(security_auth, 'authenticate_user'):
            print("   📍 authenticate_user найден в security.auth")
        else:
            print("   ❌ authenticate_user НЕ найден в security.auth")
    except ImportError as e:
        print(f"❌ Не удалось импортировать security.auth: {e}")

    try:
        from src.services import auth_service as service_auth
        print("✅ src.services.auth_service импортирован")
        if hasattr(service_auth, 'authenticate_user'):
            print("   📍 authenticate_user найден в auth_service")
        else:
            print("   ❌ authenticate_user НЕ найден в auth_service")
    except ImportError as e:
        print(f"❌ Не удалось импортировать auth_service: {e}")

# pytest tests/test_mock_diagnostic.py --html=report.html --self-contained-html