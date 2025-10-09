# tests/test_table_creation.py
import pytest
import asyncio
from sqlalchemy import text


@pytest.mark.asyncio
async def test_tables_created(db_session):
    """Тест что таблицы создаются корректно"""
    # Проверяем что таблица users существует
    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    users_table = result.scalar_one_or_none()
    assert users_table == 'users'
    print("✅ Таблица users существует")

    # Проверяем что таблица webinars существует
    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='webinars'"))
    webinars_table = result.scalar_one_or_none()
    assert webinars_table == 'webinars'
    print("✅ Таблица webinars существует")

    # Проверяем создание пользователя
    from src.database.models import User
    import uuid

    unique_id = uuid.uuid4().hex[:8]
    test_user = User(
        email=f"test_{unique_id}@example.com",
        phone=f"+7999{unique_id}",
        username=f"user_{unique_id}",
        secret_code="5678",
        hashed_password="mock_hash_TestPass123!",
        is_active=True
    )

    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    assert test_user.id is not None
    print(f"✅ Пользователь создан: {test_user.id}")

    # Очистка
    await db_session.delete(test_user)
    await db_session.commit()

# pytest tests/test_table_creation.py --html=report.html --self-contained-html