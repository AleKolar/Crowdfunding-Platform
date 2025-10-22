# src/tasks/tasks.py
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import logging
import asyncio

from src.database import models
from src.security.config import settings
from src.services.email_service import email_service

from src.services.template_service import template_service
from src.tasks.celery_app import celery_app
from src.tasks.db_operations import sync_webinar_repository, sync_notification_service

logger = logging.getLogger(__name__)

# Настройка БД для Celery (синхронная)
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("asyncpg", "psycopg2")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_async(coro):
    """Универсальная функция для запуска асинхронного кода в Celery"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        async def wrapper():
            return await coro

        return asyncio.create_task(wrapper())
    else:
        return loop.run_until_complete(coro)


# ========== EMAIL ЗАДАЧИ ==========

@celery_app.task
def send_welcome_email(user_email: str, username: str):
    """Отправка приветственного письма через Celery"""
    try:
        logger.info(f"👋 Sending welcome email to {user_email}")

        from src.services.email_service import email_service

        success = email_service.send_welcome_email(
            to_email=user_email,
            username=username
        )

        logger.info(f"✅ Welcome email sent to {user_email}: {success}")
        return success

    except Exception as e:
        logger.error(f"❌ Error sending welcome email: {e}")
        return False


@celery_app.task
def send_verification_codes_task(user_email: str, username: str, verification_code: str):
    """Отправка кодов подтверждения через Celery"""
    try:
        logger.info(f"🔐 Sending verification code to {user_email}")

        from src.services.email_service import email_service

        success = email_service.send_verification_code_email(
            to_email=user_email,
            username=username,
            verification_code=verification_code
        )

        logger.info(f"✅ Verification code sent to {user_email}: {success}")
        return success

    except Exception as e:
        logger.error(f"❌ Error sending verification code: {e}")
        return False


# ========== ПЕРИОДИЧЕСКИЕ ЗАДАЧИ ==========

@celery_app.task
def send_webinar_reminders():
    """Отправка напоминаний о вебинарах (использует синхронные репозитории)"""
    db = SessionLocal()
    try:
        webinars = sync_webinar_repository.get_upcoming_webinars_for_reminders(db)
        reminder_count = 0

        for webinar in webinars:
            registrations = sync_webinar_repository.get_registrations_for_reminder(db, webinar.id)

            for registration in registrations:
                try:
                    # Создаем уведомление через синхронный сервис
                    sync_notification_service.create_notification(
                        db=db,
                        user_id=registration.user_id,
                        title="🔔 Вебинар скоро начнется",
                        message=f"Вебинар '{webinar.title}' начинается через 1 час",
                        notification_type="webinar_reminder",
                        related_entity_type="webinar",
                        related_entity_id=webinar.id,
                        action_url=f"{settings.PLATFORM_URL}/webinars/{webinar.id}/join"
                    )

                    # Отправляем email напоминание
                    send_webinar_reminder_email.delay(
                        user_email=registration.user.email,
                        username=registration.user.username,
                        webinar_title=webinar.title,
                        scheduled_at=webinar.scheduled_at,
                        webinar_id=webinar.id
                    )

                    sync_webinar_repository.mark_reminder_sent(db, registration.id)
                    reminder_count += 1

                except Exception as e:
                    logger.error(f"❌ Error processing registration {registration.id}: {e}")
                    continue

        logger.info(f"✅ Webinar reminders sent: {reminder_count}")
        return reminder_count

    except Exception as e:
        logger.error(f"❌ Error sending webinar reminders: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def send_webinar_reminder_email(user_email: str, username: str, webinar_title: str, scheduled_at: datetime, webinar_id: int):
    """Email напоминание о вебинаре"""
    try:
        logger.info(f"📅 Sending webinar reminder to {user_email}")

        # ✅ СИНХРОННЫЙ вызов
        success = email_service.send_email(
            to_email=user_email,
            subject=f"🔔 Напоминание: вебинар '{webinar_title}'",
            html_content=template_service.render_email_template(
                "webinar_reminder.html",
                username=username,
                webinar_title=webinar_title,
                scheduled_at=scheduled_at.strftime("%d.%m.%Y в %H:%M"),
                webinar_url=f"{settings.PLATFORM_URL}/webinars/{webinar_id}/join"
            )
        )

        if success:
            logger.info(f"✅ Webinar reminder sent to {user_email}")
        else:
            logger.error(f"❌ Failed to send webinar reminder to {user_email}")

        return success

    except Exception as e:
        logger.error(f"❌ Error sending webinar reminder: {e}")
        return False


@celery_app.task
def process_email_queue():
    """Обработка очереди email"""
    db = SessionLocal()
    try:
        pending_emails = db.scalars(
            select(models.EmailQueue).where(
                models.EmailQueue.status == "pending"
            ).order_by(
                models.EmailQueue.priority.asc(),
                models.EmailQueue.created_at.asc()
            ).limit(10)
        ).all()

        processed_count = 0

        for email_job in pending_emails:
            try:
                # ✅ СИНХРОННЫЙ вызов
                success = email_service.send_email(
                    to_email=email_job.email,
                    subject=email_job.subject,
                    html_content=email_job.template_data.get("message", "")
                )

                if success:
                    email_job.status = "sent"
                    email_job.sent_at = datetime.now()
                    processed_count += 1
                    logger.info(f"✅ Email sent to {email_job.email}")
                else:
                    email_job.status = "failed"
                    email_job.error_message = "SMTP error"
                    logger.error(f"❌ Failed to send email to {email_job.email}")

                db.commit()

            except Exception as e:
                logger.error(f"❌ Error processing email {email_job.id}: {e}")
                email_job.status = "failed"
                email_job.error_message = str(e)
                db.commit()

        logger.info(f"✅ Email queue processed: {processed_count} emails")
        return processed_count

    except Exception as e:
        logger.error(f"❌ Error processing email queue: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


@celery_app.task
def update_project_rankings():
    """Обновление рейтингов и топа проектов"""
    db = SessionLocal()
    try:
        logger.info("🏆 Updating project rankings...")

        from sqlalchemy import case, desc

        # Обновляем рейтинг проектов на основе суммы донатов
        project_rankings = db.execute(
            select(
                models.Project.id,
                func.sum(models.Donation.amount).label('total_raised')
            ).select_from(
                models.Project
            ).join(
                models.Donation,
                models.Donation.project_id == models.Project.id
            ).where(
                models.Donation.status == 'completed'
            ).group_by(
                models.Project.id
            ).order_by(
                desc('total_raised')
            )
        ).fetchall()

        # Обновляем позиции в рейтинге
        for rank, (project_id, total_raised) in enumerate(project_rankings, 1):
            project = db.scalar(
                select(models.Project).where(models.Project.id == project_id)
            )
            if project:
                project.ranking_position = rank
                project.popularity_score = total_raised or 0

        db.commit()

        logger.info(f"✅ Project rankings updated: {len(project_rankings)} projects ranked")
        return {"projects_ranked": len(project_rankings)}

    except Exception as e:
        logger.error(f"❌ Error updating project rankings: {e}")
        db.rollback()
        return False
    finally:
        db.close()

@celery_app.task
def cleanup_old_data():
    """Очистка устаревших данных"""
    db = SessionLocal()
    try:
        # Очистка старых уведомлений (старше 30 дней)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        deleted_notifications = db.execute(
            delete(models.Notification).where(
                models.Notification.created_at < thirty_days_ago
            )
        ).rowcount

        # Очистка отправленных email (старше 7 дней)
        seven_days_ago = datetime.now() - timedelta(days=7)
        deleted_emails = db.execute(
            delete(models.EmailQueue).where(
                models.EmailQueue.sent_at < seven_days_ago
            )
        ).rowcount

        db.commit()
        logger.info(f"✅ Cleanup completed: {deleted_notifications} notifications, {deleted_emails} emails")
        return {"notifications": deleted_notifications, "emails": deleted_emails}

    except Exception as e:
        logger.error(f"❌ Error cleaning up old data: {e}")
        db.rollback()
        return {"notifications": 0, "emails": 0}
    finally:
        db.close()


@celery_app.task
def update_project_statistics():
    """Обновление статистики проектов на основе донатов"""
    db = SessionLocal()
    try:
        logger.info("📊 Updating project statistics from donations...")

        # 1. Сумма донатов по каждому проекту
        from sqlalchemy import func, desc

        project_stats = db.execute(
            select(
                models.Donation.project_id,
                func.count(models.Donation.id).label('donations_count'),
                func.sum(models.Donation.amount).label('total_raised'),
                func.avg(models.Donation.amount).label('avg_donation'),
                func.max(models.Donation.amount).label('max_donation')
            ).where(
                models.Donation.status == 'completed'
            ).group_by(
                models.Donation.project_id
            ).order_by(
                desc('total_raised')  # Сортировка по сумме донатов (от большего к меньшему)
            )
        ).fetchall()

        updated_count = 0

        for stat in project_stats:
            project_id, donations_count, total_raised, avg_donation, max_donation = stat

            # Находим проект
            project = db.scalar(
                select(models.Project).where(models.Project.id == project_id)
            )

            if project:
                # Обновляем статистику проекта
                project.total_raised = total_raised or 0
                project.donations_count = donations_count or 0
                project.avg_donation = avg_donation or 0
                project.max_donation = max_donation or 0

                # Обновляем процент завершения если есть цель
                if project.goal_amount and project.goal_amount > 0:
                    project.completion_percentage = min(
                        round((total_raised / project.goal_amount) * 100, 2),
                        100.0
                    )

                updated_count += 1

        # 2. Топ донаты за последние 24 часа
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        recent_large_donations = db.scalars(
            select(models.Donation).where(
                models.Donation.status == 'completed',
                models.Donation.created_at >= twenty_four_hours_ago,
                models.Donation.amount >= 1000  # Крупные донаты (от 1000)
            ).order_by(
                desc(models.Donation.amount)
            ).limit(10)
        ).all()

        # Логируем крупные донаты
        for donation in recent_large_donations:
            logger.info(f"💰 Large donation: {donation.amount} to project {donation.project_id}")

        # 3. Статистика по методам оплаты
        payment_methods_stats = db.execute(
            select(
                models.Donation.payment_method,
                func.count(models.Donation.id).label('count'),
                func.sum(models.Donation.amount).label('total')
            ).where(
                models.Donation.status == 'completed'
            ).group_by(
                models.Donation.payment_method
            )
        ).fetchall()

        # Логируем статистику по методам оплаты
        for method_stat in payment_methods_stats:
            method, count, total = method_stat
            logger.info(f"💳 Payment method {method}: {count} donations, total {total}")

        db.commit()

        logger.info(f"✅ Project statistics updated: {updated_count} projects, "
                    f"{len(recent_large_donations)} large donations in 24h, "
                    f"{len(payment_methods_stats)} payment methods")

        return {
            "projects_updated": updated_count,
            "large_donations_24h": len(recent_large_donations),
            "payment_methods": len(payment_methods_stats)
        }

    except Exception as e:
        logger.error(f"❌ Error updating project statistics: {e}")
        db.rollback()
        return False
    finally:
        db.close()


# ========== УВЕДОМЛЕНИЯ Websocket ==========

@celery_app.task
def create_platform_notification(user_id: int, title: str, message: str, notification_type: str):
    """Создание уведомления на платформе + WebSocket пуш"""
    db = SessionLocal()
    try:
        # Сохраняем уведомление в БД
        notification = models.Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(f"✅ Platform notification created for user {user_id}")

        # Отправляем пуш
        push_data = {
            "type": "notification",
            "notification_id": notification.id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "created_at": notification.created_at.isoformat(),
            "is_read": False
        }

        # Отправляем через Redis pub/sub
        import redis
        import json

        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        r.publish(f'user_{user_id}', json.dumps(push_data))

        logger.info(f"📢 WebSocket push sent to user {user_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creating platform notification: {e}")
        db.rollback()
        return False
    finally:
        db.close()


