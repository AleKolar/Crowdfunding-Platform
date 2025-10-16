# src/tasks/db_operations.py
import logging
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.database import models

logger = logging.getLogger(__name__)

# СИНХРОННОЕ подключение к БД для Celery
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_sync_db():
    """Синхронная сессия БД для Celery"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# СИНХРОННЫЕ версии методов репозиториев
class SyncWebinarRepository:
    def get_upcoming_webinars_for_reminders(self, db):
        """Синхронная версия - получение вебинаров для напоминаний"""
        from datetime import datetime, timedelta

        now = datetime.now()
        reminder_start = now + timedelta(hours=1)  # За 1 час до начала

        webinars = db.scalars(
            select(models.Webinar).where(
                models.Webinar.scheduled_at.between(now, reminder_start),
                models.Webinar.status == "scheduled"
            )
        ).all()

        return webinars

    def get_registrations_for_reminder(self, db, webinar_id):
        """Синхронная версия - получение регистраций для напоминаний"""
        registrations = db.scalars(
            select(models.WebinarRegistration).where(
                models.WebinarRegistration.webinar_id == webinar_id,
                models.WebinarRegistration.reminder_sent == False
            )
        ).all()

        return registrations

    def mark_reminder_sent(self, db, registration_id):
        """Синхронная версия - отметка о отправленном напоминании"""
        registration = db.scalar(
            select(models.WebinarRegistration).where(
                models.WebinarRegistration.id == registration_id
            )
        )
        if registration:
            registration.reminder_sent = True
            db.commit()


sync_webinar_repository = SyncWebinarRepository()


class SyncNotificationService:
    def create_notification(self, db, user_id, title, message, notification_type,
                            related_entity_type=None, related_entity_id=None,
                            action_url=None, meta_data=None):
        """Синхронная версия - создание уведомления"""
        notification = models.Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            action_url=action_url,
            meta_data=meta_data or {},
            is_read=False
        )

        db.add(notification)
        db.commit()
        return notification


sync_notification_service = SyncNotificationService()