from src.security.auth import get_password_hash, verify_password


def test_auth_mocks_work():
    """Тест что моки для аутентификации работают правильно"""
    # Тестируем моки
    password = "TestPass123!"
    hashed = get_password_hash(password)

    # Проверяем что возвращается фиксированный хеш (наш мок)
    assert hashed == "mock_hashed_password_12345"
    assert hashed.startswith("mock_hashed_")

    # Проверяем что верификация всегда возвращает True (наш мок)
    result = verify_password(password, hashed)
    assert result is True

    # Даже с неверными данными возвращает True (поведение мока)
    result2 = verify_password("completely_wrong", "totally_different_hash")
    assert result2 is True

    print("✅ Моки аутентификации работают корректно")

# pytest tests/tests_auth/test_auth_mocks.py -v -s
# pytest tests/tests_auth/test_auth_mocks.py --html=report.html