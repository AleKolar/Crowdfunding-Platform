# src/tests/test_repositories/test_user_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.user_repository import user_repository


class TestUserRepository:

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession, test_user):
        """Тест получения пользователя по ID"""
        # Act
        user = await user_repository.get_user_by_id(db_session, test_user.id)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Тест получения несуществующего пользователя"""
        # Act
        user = await user_repository.get_user_by_id(db_session, 9999)

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession, test_user):
        """Тест получения пользователя по email"""
        # Act
        user = await user_repository.get_user_by_email(db_session, test_user.email)

        # Assert
        assert user is not None
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_phone(self, db_session: AsyncSession, test_user):
        """Тест получения пользователя по телефону"""
        # Act
        user = await user_repository.get_user_by_phone(db_session, test_user.phone)

        # Assert
        assert user is not None
        assert user.phone == test_user.phone

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session: AsyncSession, test_user):
        """Тест получения пользователя по username"""
        # Act
        user = await user_repository.get_user_by_username(db_session, test_user.username)

        # Assert
        assert user is not None
        assert user.username == test_user.username

    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession, test_user):
        """Тест обновления пользователя"""
        # Arrange
        new_username = "updated_username"

        # Act
        updated_user = await user_repository.update_user(
            db_session, test_user.id, {"username": new_username}
        )

        # Assert
        assert updated_user is not None
        assert updated_user.username == new_username
        assert updated_user.email == test_user.email  # остальные поля не изменились

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session: AsyncSession):
        """Тест обновления несуществующего пользователя"""
        # Act
        updated_user = await user_repository.update_user(
            db_session, 9999, {"username": "new_username"}
        )

        # Assert
        assert updated_user is None

    @pytest.mark.asyncio
    async def test_get_users_by_ids(self, db_session: AsyncSession, test_user):
        """Тест получения пользователей по списку IDs"""
        # Act
        users = await user_repository.get_users_by_ids(db_session, [test_user.id])

        # Assert
        assert len(users) == 1
        assert users[0].id == test_user.id

    @pytest.mark.asyncio
    async def test_get_users_by_ids_empty(self, db_session: AsyncSession):
        """Тест получения пользователей по пустому списку IDs"""
        # Act
        users = await user_repository.get_users_by_ids(db_session, [])

        # Assert
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_search_users(self, db_session: AsyncSession, test_user):
        """Тест поиска пользователей"""
        # Act
        users_by_email = await user_repository.search_users(db_session, test_user.email)
        users_by_username = await user_repository.search_users(db_session, test_user.username)

        # Assert
        assert len(users_by_email) == 1
        assert users_by_email[0].email == test_user.email

        assert len(users_by_username) == 1
        assert users_by_username[0].username == test_user.username

    @pytest.mark.asyncio
    async def test_deactivate_user(self, db_session: AsyncSession, test_user):
        """Тест деактивации пользователя"""
        # Act
        result = await user_repository.deactivate_user(db_session, test_user.id)

        # Assert
        assert result is True

        # Проверяем, что пользователь действительно деактивирован
        deactivated_user = await user_repository.get_user_by_id(db_session, test_user.id)
        assert deactivated_user.is_active is False

    @pytest.mark.asyncio
    async def test_activate_user(self, db_session: AsyncSession, test_user):
        """Тест активации пользователя"""
        # Arrange - сначала деактивируем
        await user_repository.deactivate_user(db_session, test_user.id)

        # Act
        result = await user_repository.activate_user(db_session, test_user.id)

        # Assert
        assert result is True

        # Проверяем, что пользователь действительно активирован
        activated_user = await user_repository.get_user_by_id(db_session, test_user.id)
        assert activated_user.is_active is True

    @pytest.mark.asyncio
    async def test_activate_already_active_user(self, db_session: AsyncSession, test_user):
        """Тест активации уже активного пользователя"""
        # Act
        result = await user_repository.activate_user(db_session, test_user.id)

        # Assert - должен вернуть False, так как пользователь уже активен
        assert result is False

# pytest tests/test_repositories/test_user_repository.py -v --html=report.html