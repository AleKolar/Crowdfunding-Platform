# src/tests/debug_user.py
import pytest


@pytest.mark.asyncio
async def test_debug_user_fixture(db_session, test_user):
    """Проверка что фикстура test_user работает"""
    print(f"🔍 test_user: id={test_user.id}, email={test_user.email}")

    # Проверяем что пользователь сохранен в БД
    from sqlalchemy import select
    from src.database.models import User

    stmt = select(User).where(User.id == test_user.id)
    result = await db_session.execute(stmt)
    db_user = result.scalar_one_or_none()

    print(f"🔍 DB user: {db_user}")
    assert db_user is not None
    assert db_user.id == test_user.id

# pytest tests/debug_user.py -v -s