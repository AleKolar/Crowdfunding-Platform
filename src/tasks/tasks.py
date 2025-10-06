# src/tasks/tasks.py
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config.settings import settings
from src.database import models

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
        # Здесь интеграция с email сервисом (SendGrid, Mailgun, etc.)
        message = MIMEMultipart("alternative")
        message["Subject"] = "Добро пожаловать в CrowdPlatform!"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = user_email

        html = f"""
        <h1>Добро пожаловать, {username}!</h1>
        <p>Спасибо за регистрацию на нашей краудфандинговой платформе.</p>
        <p>Теперь вы можете:</p>
        <ul>
            <li>Создавать свои проекты</li>
            <li>Участвовать в вебинарах</li>
            <li>Поддерживать интересные идеи</li>
        </ul>
        """

        message.attach(MIMEText(html, "html"))

        # В development просто логируем
        print(f"📧 Welcome email to {user_email}: {html}")

        # В production:
        # with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        #     server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        #     server.send_message(message)

    except Exception as e:
        print(f"Error sending welcome email: {e}")


@celery.task
def notify_webinar_registrants(webinar_id: int):
    """Уведомление зарегистрированных на вебинар"""
    db = SessionLocal()
    try:
        webinar = db.scalar(
            select(models.Webinar)
            .where(models.Webinar.id == webinar_id)
        )

        if not webinar:
            return

        registrations = db.scalars(
            select(models.WebinarRegistration)
            .where(models.WebinarRegistration.webinar_id == webinar_id)
        ).all()

        for registration in registrations:
            # Внутриплатформенное уведомление
            notification = models.Notification(
                user_id=registration.user_id,
                title="Напоминание о вебинаре",
                message=f"Вебинар '{webinar.title}' начинается через 1 час",
                notification_type="webinar_reminder",
                related_entity_type="webinar",
                related_entity_id=webinar_id
            )
            db.add(notification)

            # Email уведомление (если включено)
            user_settings = db.scalar(
                select(models.UserSettings)
                .where(models.UserSettings.user_id == registration.user_id)
            )

            if user_settings and user_settings.email_notifications:
                send_webinar_reminder_email.delay(
                    registration.user.email,
                    webinar.title,
                    webinar.scheduled_at
                )

        db.commit()

    finally:
        db.close()


@celery.task
def send_webinar_reminder_email(user_email: str, webinar_title: str, scheduled_at: datetime):
    """Email напоминание о вебинаре"""
    # Аналогично send_welcome_email
    print(f"📧 Webinar reminder to {user_email}: {webinar_title} at {scheduled_at}")


@celery.task
def notify_followers_new_post(creator_id: int, post_id: int):
    """Уведомление подписчиков о новом посте"""
    db = SessionLocal()
    try:
        subscriptions = db.scalars(
            select(models.Subscription)
            .where(models.Subscription.creator_id == creator_id)
        ).all()

        post = db.scalar(
            select(models.Post).where(models.Post.id == post_id)
        )

        for subscription in subscriptions:
            notification = models.Notification(
                user_id=subscription.subscriber_id,
                title="Новый пост от автора",
                message=f"Автор опубликовал новый контент",
                notification_type="new_post",
                related_entity_type="post",
                related_entity_id=post_id
            )
            db.add(notification)

            # WebSocket уведомление в реальном времени
            send_websocket_notification.delay(
                subscription.subscriber_id,
                "new_post",
                {"post_id": post_id, "creator_id": creator_id}
            )

        db.commit()

    finally:
        db.close()


@celery.task
def send_websocket_notification(user_id: int, notification_type: str, data: dict):
    """Отправка уведомления через WebSocket"""
    import redis
    import json

    r = redis.Redis(host='redis', port=6379, db=0)

    message = {
        'user_id': user_id,
        'type': notification_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }

    r.publish(f'user_{user_id}', json.dumps(message))


@celery.task
def send_websocket_notification(user_id: int, notification_type: str, data: dict):
    """Отправка уведомления через WebSocket"""
    import redis
    import json
    from datetime import datetime

    try:
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

        message = {
            'user_id': user_id,
            'type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        # Публикуем в Redis канал
        r.publish(f'user_{user_id}', json.dumps(message))

        # Логируем отправку
        print(f"WebSocket notification sent to user {user_id}: {notification_type}")

    except Exception as e:
        print(f"Error sending WebSocket notification: {e}")