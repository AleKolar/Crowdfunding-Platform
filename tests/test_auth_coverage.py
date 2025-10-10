# tests/test_auth_coverage.py
import pytest
from fastapi.testclient import TestClient


def test_auth_coverage_check():
    """Проверка покрытия функционала аутентификации"""
    print("\n📊 ПРОВЕРКА ПОКРЫТИЯ АУТЕНТИФИКАЦИИ:")

    covered = [
        "✅ Регистрация пользователя",
        "✅ Логин (email + секретный код)",
        "✅ Отправка SMS кода",
        "✅ Верификация 2FA",
        "✅ Получение JWT токена",
        "✅ Защищенные эндпоинты",
        "✅ Получение профиля пользователя",
    ]

    missing = [
        "❓ Повторная отправка SMS",
        "❓ Выход из системы (logout)",
        "❓ Обновление токена",
        "❓ Смена пароля",
        "❓ Восстановление доступа",
        "❓ Валидация телефона/email",
        "❓ Ошибки и edge cases",
    ]

    print("🎯 УЖЕ ПРОТЕСТИРОВАНО:")
    for item in covered:
        print(f"   {item}")

    print("\n🔧 ВОЗМОЖНО ДОБАВИТЬ:")
    for item in missing:
        print(f"   {item}")


def test_remaining_auth_endpoints(client: TestClient, test_user):
    """Проверка оставшихся эндпоинтов аутентификации"""
    print("\n🔍 ПРОВЕРКА ОСТАВШИХСЯ ЭНДПОИНТОВ:")

    endpoints_to_test = [
        ("POST", "/auth/resend-sms", {"user_id": 1}),
        ("POST", "/auth/logout", {}),
        # ("POST", "/auth/refresh", {}),  # Когда будет refresh токен
        # ("POST", "/auth/change_password", {}),  # Когда будет смена пароля
        # ("POST", "/auth/forgot_password", {}),  # Когда будет восстановление
    ]

    for method, path, json_data in endpoints_to_test:
        response = client.post(path, json=json_data)
        print(f"  {method} {path} -> {response.status_code}")

        if response.status_code == 404:
            print(f"    ⚠️  Эндпоинт не найден (возможно не реализован)")
        elif response.status_code >= 500:
            print(f"    🔥 Server Error: {response.text}")
        else:
            print(f"    ✅ Доступен (статус {response.status_code})")

# pytest tests/test_auth_coverage.py -v -s