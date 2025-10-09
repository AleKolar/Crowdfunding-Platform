# src/tests/conftest.py
import os
import sys
import asyncio
from datetime import datetime, timedelta

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

# Мокаем LiveKit ДО импорта основного приложения
import sys
from unittest.mock import MagicMock

# Создаем мок для livekit
mock_livekit = MagicMock()
mock_livekit.api.AccessToken = MagicMock
mock_livekit.api.access_token.VideoGrants = MagicMock

sys.modules['livekit'] = mock_livekit
sys.modules['livekit.api'] = mock_livekit.api
sys.modules['livekit.api.access_token'] = mock_livekit.api.access_token

try:
    from main import app as main_app
    from src.database.postgres import get_db
    from src.database.models.base import Base
    from src.endpoints.auth import auth_router
    from src.endpoints.payments import payments_router
    from src.endpoints.projects import projects_router

    # ✅ ДОБАВЛЯЕМ ИМПОРТЫ НОВЫХ РОУТЕРОВ (если они существуют)
    try:
        from src.endpoints.comments import comments_router

        COMMENTS_AVAILABLE = True
        print("✅ Comments router импортирован")
    except ImportError:
        COMMENTS_AVAILABLE = False
        print("⚠️ Comments router не найден")

    try:
        from src.endpoints.likes import likes_router

        LIKES_AVAILABLE = True
        print("✅ Likes router импортирован")
    except ImportError:
        LIKES_AVAILABLE = False
        print("⚠️ Likes router не найден")

    from src.security.auth import get_current_user

    print("✅ Все модули успешно импортированы")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    raise


# Моки для функций хеширования паролей
def mock_get_password_hash(password):
    """Мок для хеширования пароля - обходит bcrypt ограничения"""
    return f"mock_hash_{password}"


def mock_verify_password(plain_password, hashed_password):
    """Мок проверки пароля"""
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
    echo=False  # Убрали echo для чистоты вывода
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

    # ✅ ДОБАВЛЯЕМ НОВЫЕ РОУТЕРЫ (если они доступны)
    if COMMENTS_AVAILABLE:
        test_app.include_router(comments_router)
        print("✅ Comments router добавлен в тестовое приложение")

    if LIKES_AVAILABLE:
        test_app.include_router(likes_router)
        print("✅ Likes router добавлен в тестовое приложение")

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
            self.phone = "+79991234567"

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
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для доступа к асинхронной тестовой сессии БД"""
    # Создаем таблицы перед каждым тестом
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    # Очищаем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> TestClient:
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
        # Возвращаем нового мока для каждого теста
        mock_user = type('MockUser', (), {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'is_active': True,
            'phone': '+79991234567'
        })()
        return mock_user

    # Создаем тестовое приложение
    test_app = create_test_app()

    # Переопределяем зависимости
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(test_app) as test_client:
        yield test_client

    # Очищаем переопределения
    test_app.dependency_overrides.clear()

    # Очищаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ✅ ДОБАВЛЕНЫ ФИКСТУРЫ ДЛЯ ТЕСТОВ

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Создает тестового пользователя для репозиториев"""
    from src.database.models import User
    import uuid

    unique_id = uuid.uuid4().hex[:8]

    user = User(
        email=f"repo_test_{unique_id}@example.com",
        phone=f"+7999{unique_id}",
        username=f"repotestuser_{unique_id}",
        secret_code="5678",
        hashed_password="mock_hash_TestPass123!",
        is_active=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user):
    """Создает тестовый проект для репозиториев"""
    from src.database.models.models_content import Project, ProjectStatus

    project = Project(
        title="Test Project",
        description="Test Description",
        short_description="Short test description",
        goal_amount=1000.0,
        current_amount=0.0,
        category="Technology",
        tags=["test", "technology"],
        status=ProjectStatus.DRAFT,
        creator_id=test_user.id,

    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    return project


@pytest.fixture
async def test_post(db_session: AsyncSession, test_user, test_project):
    """Создает тестовый пост для репозиториев"""
    from src.database.models.models_content import Post, PostType

    post = Post(
        content="Test Content",
        author_id=test_user.id,
        project_id=test_project.id,
        post_type=PostType.UPDATE,

    )

    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    return post


@pytest.fixture
async def test_webinar(db_session: AsyncSession, test_user):
    """Создает тестовый вебинар"""
    from src.database import models

    webinar = models.Webinar(
        title="Test Webinar",
        description="Test Description",
        scheduled_at=datetime.now() + timedelta(days=1),
        duration=60,
        max_participants=100,
        creator_id=test_user.id,
        status="scheduled"
        # is_public не нужно - его нет в модели
    )

    db_session.add(webinar)
    await db_session.commit()
    await db_session.refresh(webinar)

    return webinar


@pytest.fixture
async def test_started_webinar(db_session: AsyncSession, test_user):
    """Создает тестовый вебинар который уже начался"""
    from src.database import models

    webinar = models.Webinar(
        title="Started Webinar",
        description="Test Description",
        scheduled_at=datetime.now() - timedelta(minutes=10),  # начался 10 минут назад
        duration=60,
        max_participants=100,
        creator_id=test_user.id,
        status="scheduled"
    )

    db_session.add(webinar)
    await db_session.commit()
    await db_session.refresh(webinar)

    return webinar


@pytest.fixture
async def test_webinar_registration(db_session: AsyncSession, test_webinar, test_user):
    """Создает тестовую регистрацию на вебинар"""
    from src.database import models

    registration = models.WebinarRegistration(
        webinar_id=test_webinar.id,
        user_id=test_user.id
    )

    db_session.add(registration)
    await db_session.commit()
    await db_session.refresh(registration)

    return registration

@pytest.fixture
def authenticated_headers():
    """✅ ФИКСТУРА ДЛЯ АУТЕНТИФИЦИРОВАННЫХ ЗАПРОСОВ"""
    return {
        "Content-Type": "application/json",
    }


# Глобальная настройка pytest для асинхронных тестов
def pytest_configure(config):
    """Конфигурация pytest для асинхронных тестов"""
    config.option.asyncio_mode = "auto"


def pytest_sessionfinish(session, exitstatus):
    """Очистка после завершения всех тестов"""
    print("🧹 Очистка после тестов завершена")