# src/tasks/tasks.py
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging
import asyncio

from src.config.settings import settings
from src.database import models
from src.repository.webinar_repository import webinar_repository
from src.services.email_service import email_service
from src.services.template_service import template_service
from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

celery = Celery('crowdfunding')
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Настройка БД
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task
def send_welcome_email(user_email: str, username: str):
    """Приветственное письмо новому пользователю"""
    try:
        subject = "🎉 Добро пожаловать в CrowdPlatform!"

        html_content = template_service.render_email_template(
            "welcome.html",
            username=username,
            platform_url=settings.PLATFORM_URL
        )

        # ✅ ИСПРАВЛЕНО: Создаем event loop для асинхронного вызова
        async def send_email_async():
            return await email_service.send_email(user_email, subject, html_content)

        # Запускаем асинхронную функцию в event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(send_email_async())

            if success:
                logger.info(f"✅ Приветственное письмо отправлено на {user_email}")
            else:
                logger.error(f"❌ Ошибка отправки приветственного письма на {user_email}")

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Ошибка отправки приветственного письма: {e}")


@celery_app.task
def send_verification_codes(user_email: str, username: str, phone: str, verification_code: str):
    """Отправка кодов подтверждения по SMS и Email"""
    try:
        # ✅ ОТПРАВКА EMAIL С КОДОМ
        async def send_verification_email():
            return await email_service.send_verification_code_email(
                to_email=user_email,
                username=username,
                verification_code=verification_code
            )

        # ✅ ОТПРАВКА SMS С КОДОМ
        async def send_verification_sms():
            from src.services.sms_service import sms_service
            return await sms_service.send_verification_code(phone, verification_code)

        # Запускаем обе отправки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            email_success = loop.run_until_complete(send_verification_email())
            sms_success = loop.run_until_complete(send_verification_sms())

            logger.info(f"🔐 Коды отправлены для {user_email}: SMS={sms_success}, Email={email_success}")

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Ошибка отправки кодов подтверждения: {e}")


@celery_app.task
def send_webinar_reminders():
    """Отправка напоминаний о вебинарах через систему уведомлений"""
    db = SessionLocal()
    try:
        from src.services.notification_service import notification_service
        webinars = webinar_repository.get_upcoming_webinars_for_reminders(db)

        for webinar in webinars:
            registrations = webinar_repository.get_registrations_for_reminder(db, webinar.id)

            for registration in registrations:
                notification_service.create_notification(
                    db=db,
                    user_id=registration.user_id,
                    title="🔔 Вебинар скоро начнется",
                    message=f"Вебинар '{webinar.title}' начинается через 1 час",
                    notification_type="webinar_reminder",
                    related_entity_type="webinar",
                    related_entity_id=webinar.id,
                    action_url=f"{settings.PLATFORM_URL}/webinars/{webinar.id}/join",
                    meta_data={
                        "webinar_title": webinar.title,
                        "scheduled_at": webinar.scheduled_at.isoformat(),
                        "webinar_id": webinar.id
                    }
                )

                webinar_repository.mark_reminder_sent(db, registration.id)

            db.commit()

    except Exception as e:
        logger.error(f"Error sending webinar reminders: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task
def send_webinar_reminder_email(user_email: str, username: str, webinar_title: str, scheduled_at: datetime,
                                webinar_id: int):
    """Email напоминание о вебинаре"""
    try:
        subject = f"🔔 Напоминание: вебинар '{webinar_title}'"

        html_content = template_service.render_email_template(
            "webinar_reminder.html",
            username=username,
            webinar_title=webinar_title,
            scheduled_at=scheduled_at.strftime("%d.%m.%Y в %H:%M"),
            duration=60,
            webinar_url=f"{settings.PLATFORM_URL}/webinars/{webinar_id}/join"
        )

        # ✅ ИСПРАВЛЕНО: Асинхронная отправка
        async def send_email_async():
            return await email_service.send_email(user_email, subject, html_content)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(send_email_async())
            if success:
                logger.info(f"✅ Напоминание о вебинаре отправлено на {user_email}")
            else:
                logger.error(f"❌ Ошибка отправки напоминания на {user_email}")
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания о вебинаре: {e}")


@celery_app.task
def process_email_queue():
    """Обработка очереди email"""
    db = SessionLocal()
    try:
        # Берем emails с высоким приоритетом сначала
        pending_emails = db.scalars(
            select(models.EmailQueue).where(
                models.EmailQueue.status == "pending"
            ).order_by(
                models.EmailQueue.priority.asc(),
                models.EmailQueue.created_at.asc()
            ).limit(10)
        ).all()

        for email_job in pending_emails:
            try:
                # ✅ ИСПРАВЛЕНО: Асинхронная отправка
                async def send_email_async():
                    return await email_service.send_email(
                        email_job.email,
                        email_job.subject,
                        email_job.template_data.get("message", "")
                    )

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(send_email_async())

                    if success:
                        email_job.status = "sent"
                        email_job.sent_at = datetime.now()
                    else:
                        email_job.status = "failed"
                        email_job.error_message = "SMTP error"

                    db.commit()

                finally:
                    loop.close()

            except Exception as e:
                email_job.retry_count += 1
                if email_job.retry_count >= email_job.max_retries:
                    email_job.status = "failed"
                    email_job.error_message = str(e)
                else:
                    email_job.status = "retrying"

                db.commit()
                logger.error(f"Error processing email queue item {email_job.id}: {e}")

    except Exception as e:
        logger.error(f"Error processing email queue: {e}")
        db.rollback()
    finally:
        db.close()

# ... остальные задачи остаются без изменений