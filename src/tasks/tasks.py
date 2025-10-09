# src/tasks/tasks.py
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging

from src.config.settings import settings
from src.database import models
from src.repository.webinar_repository import webinar_repository
from src.services.email_service import email_service
from src.services.template_service import template_service

logger = logging.getLogger(__name__)

celery = Celery('crowdfunding')
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Настройка БД
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery.task
def send_welcome_email(user_email: str, username: str):
    """Приветственное письмо новому пользователю"""
    try:
        subject = "🎉 Добро пожаловать в CrowdPlatform!"

        html_content = template_service.render_email_template(
            "welcome.html",
            username=username,
            platform_url=settings.PLATFORM_URL
        )

        if settings.ENVIRONMENT == "production":
            success = email_service.send_email(user_email, subject, html_content)
            if not success:
                logger.error(f"Failed to send welcome email to {user_email}")
        else:
            logger.info(f"📧 Welcome email prepared for {user_email}")

    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")


@celery.task
def send_webinar_reminders():
    """Отправка напоминаний о вебинарах через систему уведомлений"""
    db = SessionLocal()
    try:
        from src.services.notification_service import notification_service
        webinars = webinar_repository.get_upcoming_webinars_for_reminders(db)

        for webinar in webinars:

            registrations = webinar_repository.get_registrations_for_reminder(db, webinar.id)

            for registration in registrations:
                # Отправляем уведомление через систему уведомлений
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


@celery.task
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
            duration=60,  # Добавляем продолжительность
            webinar_url=f"{settings.PLATFORM_URL}/webinars/{webinar_id}/join"
        )

        if settings.ENVIRONMENT == "production":
            email_service.send_email(user_email, subject, html_content)
        else:
            logger.info(f"📧 Webinar reminder prepared for {user_email}")

    except Exception as e:
        logger.error(f"Error sending webinar reminder: {e}")


@celery.task
def process_email_queue():
    """ НОВАЯ ЗАДАЧА: Обработка очереди email"""
    db = SessionLocal()
    try:
        from src.services.email_service import email_service

        # Берем emails с высоким приоритетом сначала
        pending_emails = db.scalars(
            select(models.EmailQueue).where(
                models.EmailQueue.status == "pending"
            ).order_by(
                models.EmailQueue.priority.asc(),
                models.EmailQueue.created_at.asc()
            ).limit(10)  # Обрабатываем по 10 за раз
        ).all()

        for email_job in pending_emails:
            try:
                # Отправляем email
                success = email_service.send_email(
                    email_job.email,
                    email_job.subject,
                    email_job.template_data.get("message", "")
                )

                if success:
                    email_job.status = "sent"
                    email_job.sent_at = datetime.now()
                else:
                    email_job.status = "failed"
                    email_job.error_message = "SMTP error"

                db.commit()

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


@celery.task
def cleanup_old_data():
    """ НОВАЯ ЗАДАЧА: Очистка устаревших данных"""
    db = SessionLocal()
    try:
        # Очистка старых уведомлений (старше 30 дней)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        old_notifications = db.scalars(
            select(models.Notification).where(
                models.Notification.created_at < thirty_days_ago
            )
        ).all()

        for notification in old_notifications:
            db.delete(notification)

        # Очистка отправленных email из очереди (старше 7 дней)
        seven_days_ago = datetime.now() - timedelta(days=7)
        old_emails = db.scalars(
            select(models.EmailQueue).where(
                models.EmailQueue.sent_at < seven_days_ago
            )
        ).all()

        for email in old_emails:
            db.delete(email)

        db.commit()
        logger.info(f"Cleaned up {len(old_notifications)} notifications and {len(old_emails)} emails")

    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        db.rollback()
    finally:
        db.close()


@celery.task
def create_platform_notification(user_id: int, title: str, message: str, notification_type: str):
    """Создание уведомления на платформе"""
    db = SessionLocal()
    try:
        notification = models.Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False
        )

        db.add(notification)
        db.commit()
        logger.info(f"Platform notification created for user {user_id}")

    except Exception as e:
        logger.error(f"Error creating platform notification: {e}")
        db.rollback()
    finally:
        db.close()


@celery.task
def notify_followers_new_post(creator_id: int, post_id: int):
    """Уведомление подписчиков о новом посте"""
    db = SessionLocal()
    try:
        subscriptions = db.scalars(
            select(models.Subscription).where(models.Subscription.creator_id == creator_id)
        ).all()

        post = db.scalar(select(models.Post).where(models.Post.id == post_id))

        if not post:
            return

        for subscription in subscriptions:
            notification = models.Notification(
                user_id=subscription.subscriber_id,
                title="Новый пост от автора",
                message=f"Автор опубликовал новый контент",
                notification_type="new_post"
            )
            db.add(notification)

        db.commit()

    except Exception as e:
        logger.error(f"Error notifying followers: {e}")
        db.rollback()
    finally:
        db.close()


@celery.task
def send_websocket_notification(user_id: int, notification_type: str, data: dict):
    """Отправка уведомления через WebSocket"""
    try:
        import redis
        import json

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

        message = {
            'user_id': user_id,
            'type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        r.publish(f'user_{user_id}', json.dumps(message))
        logger.info(f"WebSocket notification sent to user {user_id}: {notification_type}")

    except Exception as e:
        logger.error(f"Error sending WebSocket notification: {e}")