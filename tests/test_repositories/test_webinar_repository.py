# src/tests/test_repositories/test_webinar_repository.py
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.repository.webinar_repository import webinar_repository
from src.database import models


class TestWebinarRepository:

    def _generate_unique_phone(self):
        """Генерация уникального номера телефона для тестов"""
        unique_part = uuid.uuid4().hex[:7]
        return f"+7999{unique_part}"

    def _generate_unique_email(self):
        """Генерация уникального email для тестов"""
        unique_part = uuid.uuid4().hex[:8]
        return f"test_{unique_part}@example.com"

    def _generate_unique_username(self):
        """Генерация уникального username для тестов"""
        unique_part = uuid.uuid4().hex[:8]
        return f"user_{unique_part}"

    @pytest.mark.asyncio
    async def test_create_and_get_webinar(self, db_session: AsyncSession, test_user):
        """Тест создания и получения вебинара"""
        # Arrange
        webinar_data = {
            "title": "Test Webinar",
            "description": "Test Description",
            "scheduled_at": datetime.now() + timedelta(days=1),
            "duration": 60,
            "max_participants": 100,
            "creator_id": test_user.id,
            "status": "scheduled"
        }

        webinar = models.Webinar(**webinar_data)
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Act
        retrieved_webinar = await webinar_repository.get_webinar_by_id(db_session, webinar.id)

        # Assert
        assert retrieved_webinar is not None
        assert retrieved_webinar.title == webinar_data["title"]
        assert retrieved_webinar.creator_id == test_user.id

    @pytest.mark.asyncio
    async def test_webinar_registration(self, db_session: AsyncSession, test_user):
        """Тест регистрации на вебинар"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration=60,
            max_participants=100,
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Act - регистрируем пользователя
        registration = await webinar_repository.create_registration(
            db_session, webinar.id, test_user.id
        )

        # Assert
        assert registration is not None
        assert registration.webinar_id == webinar.id
        assert registration.user_id == test_user.id

        # Проверяем, что регистрация найдена
        found_registration = await webinar_repository.get_user_registration(
            db_session, webinar.id, test_user.id
        )
        assert found_registration is not None

    @pytest.mark.asyncio
    async def test_get_webinar_registrations_count(self, db_session: AsyncSession, test_user):
        """Тест подсчета регистраций на вебинар"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration=60,
            max_participants=100,
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Act - создаем несколько регистраций
        await webinar_repository.create_registration(db_session, webinar.id, test_user.id)

        # Создаем второго пользователя для теста с уникальными данными
        another_user = models.User(
            email=self._generate_unique_email(),
            phone=self._generate_unique_phone(),
            username=self._generate_unique_username(),
            secret_code="1111",
            hashed_password="mock_hash_password"
        )
        db_session.add(another_user)
        await db_session.commit()
        await db_session.refresh(another_user)

        await webinar_repository.create_registration(db_session, webinar.id, another_user.id)

        # Act - получаем количество регистраций
        count = await webinar_repository.get_webinar_registrations_count(db_session, webinar.id)

        # Assert
        assert count == 2

    @pytest.mark.asyncio
    async def test_webinar_with_computed_fields(self, db_session: AsyncSession, test_user):
        """Тест вычисляемых полей вебинара"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(hours=2),  # upcoming
            duration=60,
            max_participants=10,
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Act
        result = await webinar_repository.get_webinar_with_computed_fields(
            db_session, webinar.id, test_user.id
        )

        # Assert
        assert result is not None
        webinar_obj, computed_fields = result

        assert computed_fields["available_slots"] == 10  # пока нет регистраций
        assert computed_fields["is_upcoming"] is True
        assert computed_fields["is_registered"] is False
        assert computed_fields["room_name"] == f"webinar_{webinar.id}"

    @pytest.mark.asyncio
    async def test_mark_attended(self, db_session: AsyncSession, test_user):
        """Тест отметки присутствия на вебинаре"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration=60,
            max_participants=100,
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        registration = await webinar_repository.create_registration(
            db_session, webinar.id, test_user.id
        )

        # Act
        result = await webinar_repository.mark_attended(db_session, webinar.id, test_user.id)

        # Assert
        assert result is True

        # Проверяем, что регистрация обновлена
        updated_registration = await webinar_repository.get_user_registration(
            db_session, webinar.id, test_user.id
        )
        assert updated_registration.attended is True

    @pytest.mark.asyncio
    async def test_delete_registration(self, db_session: AsyncSession, test_user):
        """Тест удаления регистрации"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration=60,
            max_participants=100,
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Создаем регистрацию
        await webinar_repository.create_registration(db_session, webinar.id, test_user.id)

        # Проверяем, что регистрация существует
        registration_before = await webinar_repository.get_user_registration(
            db_session, webinar.id, test_user.id
        )
        assert registration_before is not None

        # Act - удаляем регистрацию
        result = await webinar_repository.delete_registration(db_session, webinar.id, test_user.id)

        # Assert
        assert result is True

        # Проверяем, что регистрации больше нет
        registration_after = await webinar_repository.get_user_registration(
            db_session, webinar.id, test_user.id
        )
        assert registration_after is None

    @pytest.mark.asyncio
    async def test_get_scheduled_webinars(self, db_session: AsyncSession, test_user):
        """Тест получения запланированных вебинаров"""
        # Arrange - создаем несколько вебинаров
        webinar1 = models.Webinar(
            title="Webinar 1",
            description="Description 1",
            scheduled_at=datetime.now() + timedelta(days=1),
            duration=60,
            max_participants=50,
            creator_id=test_user.id,
            status="scheduled"
        )

        webinar2 = models.Webinar(
            title="Webinar 2",
            description="Description 2",
            scheduled_at=datetime.now() + timedelta(days=2),
            duration=90,
            max_participants=100,
            creator_id=test_user.id,
            status="scheduled"
        )

        # Вебинар с другим статусом (не должен попасть в результаты)
        webinar3 = models.Webinar(
            title="Webinar 3",
            description="Description 3",
            scheduled_at=datetime.now() + timedelta(days=3),
            duration=120,
            max_participants=200,
            creator_id=test_user.id,
            status="completed"  # не scheduled!
        )

        db_session.add_all([webinar1, webinar2, webinar3])
        await db_session.commit()

        # Act
        scheduled_webinars = await webinar_repository.get_scheduled_webinars(db_session)

        # Assert
        assert len(scheduled_webinars) == 2
        webinar_titles = [w.title for w in scheduled_webinars]
        assert "Webinar 1" in webinar_titles
        assert "Webinar 2" in webinar_titles
        assert "Webinar 3" not in webinar_titles  # completed не должен быть в результатах

    @pytest.mark.asyncio
    async def test_webinar_computed_fields_with_registrations(self, db_session: AsyncSession, test_user):
        """Тест вычисляемых полей с существующими регистрациями"""
        # Arrange
        webinar = models.Webinar(
            title="Test Webinar",
            description="Test Description",
            scheduled_at=datetime.now() + timedelta(hours=1),
            duration=60,
            max_participants=2,  # всего 2 места
            creator_id=test_user.id,
            status="scheduled"
        )
        db_session.add(webinar)
        await db_session.commit()
        await db_session.refresh(webinar)

        # Создаем первого пользователя и регистрируем
        user1 = models.User(
            email=self._generate_unique_email(),
            phone=self._generate_unique_phone(),
            username=self._generate_unique_username(),
            secret_code="1111",
            hashed_password="mock_hash_password"
        )
        db_session.add(user1)
        await db_session.commit()
        await db_session.refresh(user1)

        await webinar_repository.create_registration(db_session, webinar.id, user1.id)

        # Act - проверяем вычисляемые поля для второго пользователя
        user2 = models.User(
            email=self._generate_unique_email(),
            phone=self._generate_unique_phone(),
            username=self._generate_unique_username(),
            secret_code="2222",
            hashed_password="mock_hash_password"
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)

        result = await webinar_repository.get_webinar_with_computed_fields(
            db_session, webinar.id, user2.id
        )

        # Assert
        assert result is not None
        webinar_obj, computed_fields = result

        assert computed_fields["available_slots"] == 1  # 2 места - 1 регистрация = 1 доступное
        assert computed_fields["is_upcoming"] is True
        assert computed_fields["is_registered"] is False  # user2 не зарегистрирован

        # Регистрируем user2 и проверяем снова
        await webinar_repository.create_registration(db_session, webinar.id, user2.id)

        result_after = await webinar_repository.get_webinar_with_computed_fields(
            db_session, webinar.id, user2.id
        )
        webinar_obj_after, computed_fields_after = result_after

        assert computed_fields_after["available_slots"] == 0  # все места заняты
        assert computed_fields_after["is_registered"] is True  # user2 теперь зарегистрирован

# pytest tests/test_repositories/test_webinar_repository.py -v --html=report.html