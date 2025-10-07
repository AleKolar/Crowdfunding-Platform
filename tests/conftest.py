# src/tests/conftest.py
import os
import sys
import asyncio
import pytest
import uuid
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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


# Моки для функций хеширования паролей
def mock_get_password_hash(password):
    """Мок для хеширования пароля - обходит bcrypt ограничения"""
    print(f"✅ MOCK get_password_hash called with: '{password}' (length: {len(password)})")
    return f"mock_hash_{password}"


def mock_verify_password(plain_password, hashed_password):
    """Мок проверки пароля"""
    print(f"✅ MOCK verify_password called with: '{plain_password}' vs '{hashed_password}'")
    if hashed_password.startswith("mock_hash_"):
        expected_password = hashed_password.replace("mock_hash_", "")
        return plain_password == expected_password
    return False


# Применяем моки к модулю аутентификации
try:
    import src.security.auth as auth_module
    auth_module.get_password_hash = mock_get_password_hash
    auth_module.verify_password = mock_verify_password
    print("✅ Моки применены к auth модулю")
except Exception as e:
    print(f"⚠️ Не удалось применить моки к auth модулю: {e}")


# Асинхронная тестовая БД (SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True  # Для отладки SQL запросов
)

TestingAsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


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
        "password": "TestPass123!",
        "secret_code": "1234"
    }


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client(current_user_mock) -> TestClient:
    """Test client с асинхронной тестовой БД"""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    async def override_get_current_user():
        return current_user_mock

    # Создаем тестовое приложение
    test_app = create_test_app()

    # Переопределяем зависимости
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(test_app) as test_client:
        yield test_client

    # Очищаем переопределения и таблицы
    test_app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для доступа к асинхронной тестовой сессии БД"""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Глобальная настройка pytest для асинхронных тестов
def pytest_configure(config):
    """Конфигурация pytest для асинхронных тестов"""
    config.option.asyncio_mode = "auto"