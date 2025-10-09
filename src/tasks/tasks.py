# src/tasks/tasks.py
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging

from src.config.settings import settings
from src.database import models
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
    """Отправка напоминаний о вебинарах"""
    db = SessionLocal()
    try:
        # Вебинары, которые начнутся через 1 час
        one_hour_from_now = datetime.now() + timedelta(hours=1)
        time_range_start = one_hour_from_now - timedelta(minutes=5)
        time_range_end = one_hour_from_now + timedelta(minutes=5)

        webinars = db.scalars(
            select(models.Webinar).where(
                models.Webinar.scheduled_at.between(time_range_start, time_range_end),
                models.Webinar.status == "scheduled"
            )
        ).all()

        for webinar in webinars:
            # Находим регистрации без отправленных напоминаний
            registrations = db.scalars(
                select(models.WebinarRegistration).where(
                    models.WebinarRegistration.webinar_id == webinar.id,
                    models.WebinarRegistration.reminder_sent == False
                )
            ).all()

            for registration in registrations:
                # Отправляем email напоминание
                send_webinar_reminder_email.delay(
                    registration.user.email,
                    registration.user.username,
                    webinar.title,
                    webinar.scheduled_at,
                    webinar.id
                )

                # Создаем платформенное уведомление
                notification = models.Notification(
                    user_id=registration.user_id,
                    title="🔔 Вебинар скоро начнется",
                    message=f"Вебинар '{webinar.title}' начинается через 1 час",
                    notification_type="webinar_reminder"
                )
                db.add(notification)

                # Помечаем как отправленное
                registration.reminder_sent = True

            db.commit()

    except Exception as e:
        logger.error(f"Error sending webinar reminders: {e}")
        db.rollback()
    finally:
        db.close()


@celery.task
def send_webinar_reminder_email(user_email: str, username: str, webinar_title: str, scheduled_at: datetime, webinar_id: int):
    """Email напоминание о вебинаре"""
    try:
        subject = f"🔔 Напоминание: вебинар '{webinar_title}'"

        html_content = template_service.render_email_template(
            "webinar_reminder.html",
            username=username,
            webinar_title=webinar_title,
            scheduled_at=scheduled_at.strftime("%d.%m.%Y в %H:%M"),
            webinar_url=f"{settings.PLATFORM_URL}/webinars/{webinar_id}/join"
        )

        if settings.ENVIRONMENT == "production":
            email_service.send_email(user_email, subject, html_content)
        else:
            logger.info(f"📧 Webinar reminder prepared for {user_email}")

    except Exception as e:
        logger.error(f"Error sending webinar reminder: {e}")


@celery.task
def send_webinar_registration_confirmation(user_email: str, username: str, webinar_title: str, scheduled_at: datetime):
    """Простое письмо подтверждения регистрации"""
    try:
        subject = f"🎉 Вы зарегистрированы на вебинар: {webinar_title}"

        html_content = f"""
        <h2>Привет, {username}!</h2>
        <p>Вы успешно зарегистрировались на вебинар:</p>
        <h3>"{webinar_title}"</h3>
        <p><strong>🗓️ Дата и время:</strong> {scheduled_at.strftime('%d.%m.%Y в %H:%M')}</p>
        <p>Мы напомним вам за 1 час до начала.</p>
        <p>--<br>Команда CrowdPlatform</p>
        """

        if settings.ENVIRONMENT == "production":
            email_service.send_email(user_email, subject, html_content)
        else:
            logger.info(f"📧 Simple registration email for {user_email}")

    except Exception as e:
        logger.error(f"Error sending registration email: {e}")


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