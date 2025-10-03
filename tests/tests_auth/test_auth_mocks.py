# tests/tests_auth/test_auth_mocks.py
import sys
import os

# Добавляем корневую директорию проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.security.auth import get_password_hash, verify_password


def test_auth_mocks_work():
    """Проверяем что моки работают"""
    password = "TestPass123!"
    hashed = get_password_hash(password)

    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verify correct: {verify_password(password, hashed)}")
    print(f"Verify wrong: {verify_password('wrong', hashed)}")

    assert hashed.startswith("mock_hash_")
    assert verify_password(password, hashed) == True
    assert verify_password("wrong", hashed) == False

# pytest tests/tests_auth/test_auth_mocks.py -v -s