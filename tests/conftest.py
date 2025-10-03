# tests/conftest.py
import os
import sys

import pytest
import uuid
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Добавляем корневую директорию проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print(f"🔧 Project root: {project_root}")

# Сначала импортируем основные модули
try:
    from main import app as main_app
    from src.database.postgres import get_db
    from src.database.models.base import Base
    from src.endpoints.auth import auth_router
    from src.endpoints.payments import payments_router
    from src.endpoints.projects import projects_router
    from src.security.auth import get_current_user

    print("✅ Все модули успешно импортированы")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    raise


# Определяем моки для функций хеширования паролей
def mock_get_password_hash(password):
    """Мок для хеширования пароля - обходит bcrypt ограничения"""
    print(f"✅ MOCK get_password_hash called with: '{password}' (length: {len(password)})")
    # Простой мок без bcrypt - возвращаем пароль с префиксом
    return f"mock_hash_{password}"


def mock_verify_password(plain_password, hashed_password):
    """Мок проверки пароля"""
    print(f"✅ MOCK verify_password called with: '{plain_password}' vs '{hashed_password}'")
    if hashed_password.startswith("mock_hash_"):
        expected_password = hashed_password.replace("mock_hash_", "")
        return plain_password == expected_password
    return False


# Применяем моки к модулю аутентификации ДО создания приложения
try:
    import src.security.auth as auth_module

    # Сохраняем оригинальные функции на случай если понадобятся
    auth_module.original_get_password_hash = auth_module.get_password_hash
    auth_module.original_verify_password = auth_module.verify_password

    # Применяем моки
    auth_module.get_password_hash = mock_get_password_hash
    auth_module.verify_password = mock_verify_password

    print("✅ Моки применены к auth модулю")
except Exception as e:
    print(f"⚠️ Не удалось применить моки к auth модулю: {e}")


# Создаем тестовое приложение
def create_test_app():
    """Создает тестовое приложение"""
    test_app = FastAPI(
        title="Test Crowdfunding Platform API",
        description="Тестовая версия",
        version="1.0.0",
    )

    # Добавляем роутеры
    test_app.include_router(auth_router)
    test_app.include_router(payments_router)
    test_app.include_router(projects_router)

    # Health check
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "environment": "test"}

    return test_app


# Тестовая БД
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def current_user_mock():
    """Фикстура мока текущего пользователя"""

    class MockUser:
        def __init__(self):
            self.id = 1
            self.email = "test@example.com"
            self.username = "testuser"
            self.is_active = True

    return MockUser()

@pytest.fixture
def valid_register_data():
    """Фикстура с валидными данными для регистрации"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{unique_id}@example.com",
        "phone": f"+7999{unique_id[:7]}",
        "username": f"user_{unique_id}",
        "is_active": True,
        "password": "TestPass123!",
        "secret_code": "123456"
    }


@pytest.fixture
def mock_project_response():
    """Фикстура с моком ответа проекта"""
    return {
        "id": 1,
        "title": "Test Project",
        "description": "Test project description",
        "short_description": "Test short description",
        "goal_amount": 5000.0,
        "category": "technology",
        "tags": ["tech", "innovation"],
        "creator_id": 1,
        "current_amount": 0.0,
        "status": "draft",
        "is_featured": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "views_count": 0,
        "likes_count": 0,
        "shares_count": 0,
        "backers_count": 0,
        "progress_percentage": 0.0,
        "days_remaining": None,
        "is_funded": False
    }


@pytest.fixture
def mock_project_with_media_response():
    """Фикстура с моком ответа проекта с медиа"""
    return {
        "id": 1,
        "title": "Test Project",
        "description": "Test project description",
        "short_description": "Test short description",
        "goal_amount": 5000.0,
        "category": "technology",
        "tags": ["tech", "innovation"],
        "creator_id": 1,
        "current_amount": 0.0,
        "status": "draft",
        "is_featured": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "views_count": 0,
        "likes_count": 0,
        "shares_count": 0,
        "backers_count": 0,
        "progress_percentage": 0.0,
        "days_remaining": None,
        "is_funded": False,
        "media": []
    }


@pytest.fixture(scope="function")
def client(current_user_mock):
    """Test client с тестовым приложением и переопределенной аутентификацией"""
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Переопределяем аутентификацию
    async def override_get_current_user():
        print(f"✅ MOCK get_current_user called, returning user: {current_user_mock.id}")
        return current_user_mock

    # Создаем тестовое приложение
    test_app = create_test_app()

    # Переопределяем зависимости
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(test_app) as test_client:
        yield test_client

    # Очищаем переопределения
    test_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Фикстура для доступа к тестовой сессии БД"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Фикстура для восстановления оригинальных функций (если понадобится)
@pytest.fixture
def restore_original_auth_functions():
    """Восстанавливает оригинальные функции аутентификации"""
    try:
        import src.security.auth as auth_module
        if hasattr(auth_module, 'original_get_password_hash'):
            auth_module.get_password_hash = auth_module.original_get_password_hash
        if hasattr(auth_module, 'original_verify_password'):
            auth_module.verify_password = auth_module.original_verify_password
        print("✅ Оригинальные функции аутентификации восстановлены")
    except Exception as e:
        print(f"⚠️ Не удалось восстановить оригинальные функции: {e}")