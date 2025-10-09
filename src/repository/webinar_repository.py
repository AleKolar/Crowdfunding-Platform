# src/repository/webinar_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List, Optional

from src.database import models


class WebinarRepository:

    async def get_webinar_by_id(self, db: AsyncSession, webinar_id: int) -> Optional[models.Webinar]:
        """Получение вебинара по ID"""
        result = await db.execute(
            select(models.Webinar).where(models.Webinar.id == webinar_id)
        )
        return result.scalar_one_or_none()

    async def get_webinar_with_registration(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> tuple[Optional[models.Webinar], Optional[models.WebinarRegistration]]:
        """Получение вебинара и информации о регистрации пользователя"""
        webinar = await self.get_webinar_by_id(db, webinar_id)
        if not webinar:
            return None, None

        registration = await self.get_user_registration(db, webinar_id, user_id)
        return webinar, registration

    async def get_user_registration(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> Optional[models.WebinarRegistration]:
        """Получение регистрации пользователя на вебинар"""
        result = await db.execute(
            select(models.WebinarRegistration).where(
                models.WebinarRegistration.webinar_id == webinar_id,
                models.WebinarRegistration.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_registration(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> models.WebinarRegistration:
        """Создание регистрации на вебинар"""
        registration = models.WebinarRegistration(
            webinar_id=webinar_id,
            user_id=user_id
        )
        db.add(registration)
        await db.commit()
        await db.refresh(registration)
        return registration

    async def delete_registration(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> bool:
        """Удаление регистрации на вебинар"""
        registration = await self.get_user_registration(db, webinar_id, user_id)
        if registration:
            await db.delete(registration)
            await db.commit()
            return True
        return False

    async def get_scheduled_webinars(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 20
    ) -> List[models.Webinar]:
        """Получение списка запланированных вебинаров"""
        result = await db.execute(
            select(models.Webinar)
            .where(models.Webinar.status == "scheduled")
            .order_by(models.Webinar.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_user_registered_webinars(
            self,
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 20
    ) -> List[models.WebinarRegistration]:
        """Получение списка вебинаров, на которые зарегистрирован пользователь"""
        result = await db.execute(
            select(models.WebinarRegistration)
            .where(models.WebinarRegistration.user_id == user_id)
            .join(models.Webinar)
            .order_by(models.Webinar.scheduled_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_attended(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> bool:
        """Пометить пользователя как присутствовавшего на вебинаре"""
        registration = await self.get_user_registration(db, webinar_id, user_id)
        if registration:
            registration.attended = True
            await db.commit()
            return True
        return False

    async def get_upcoming_webinars_for_reminders(
            self,
            db: AsyncSession,
            hours_before: int = 1
    ) -> List[models.Webinar]:
        """Получение вебинаров для отправки напоминаний"""
        reminder_time = datetime.now() + timedelta(hours=hours_before)
        time_range_start = reminder_time - timedelta(minutes=5)
        time_range_end = reminder_time + timedelta(minutes=5)

        result = await db.execute(
            select(models.Webinar).where(
                models.Webinar.scheduled_at.between(time_range_start, time_range_end),
                models.Webinar.status == "scheduled"
            )
        )
        return result.scalars().all()

    async def get_registrations_for_reminder(
            self,
            db: AsyncSession,
            webinar_id: int
    ) -> List[models.WebinarRegistration]:
        """Получение регистраций для отправки напоминаний"""
        result = await db.execute(
            select(models.WebinarRegistration).where(
                models.WebinarRegistration.webinar_id == webinar_id,
                models.WebinarRegistration.reminder_sent == False
            )
        )
        return result.scalars().all()

    async def mark_reminder_sent(
            self,
            db: AsyncSession,
            registration_id: int
    ) -> None:
        """Пометить напоминание как отправленное"""
        result = await db.execute(
            select(models.WebinarRegistration).where(
                models.WebinarRegistration.id == registration_id
            )
        )
        registration = result.scalar_one_or_none()
        if registration:
            registration.reminder_sent = True
            await db.commit()

    async def check_webinar_exists(
            self,
            db: AsyncSession,
            webinar_id: int
    ) -> bool:
        """Проверка существования вебинара"""
        webinar = await self.get_webinar_by_id(db, webinar_id)
        return webinar is not None

    async def check_user_registered(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_id: int
    ) -> bool:
        """Проверка регистрации пользователя на вебинар"""
        registration = await self.get_user_registration(db, webinar_id, user_id)
        return registration is not None


webinar_repository = WebinarRepository()