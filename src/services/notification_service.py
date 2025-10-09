# src/services/notification_service.py
import redis
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Row, RowMapping

from src.config.settings import settings
from src.database import models

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    # ==================== REDIS АНОНСЫ ====================

    def create_webinar_announcement(self, webinar_data: Dict[str, Any]) -> str:
        """Создание оповещения о вебинаре на главной странице"""
        announcement_id = f"webinar_announcement_{webinar_data['id']}"

        announcement = {
            'id': webinar_data['id'],
            'title': webinar_data['title'],
            'description': webinar_data.get('description', ''),
            'scheduled_at': webinar_data['scheduled_at'].isoformat() if hasattr(webinar_data['scheduled_at'],
                                                                                'isoformat') else webinar_data[
                'scheduled_at'],
            'duration': webinar_data.get('duration', 60),
            'max_participants': webinar_data.get('max_participants', 100),
            'type': 'webinar_announcement'
        }

        # Сохраняем в Redis на 7 дней
        self.redis_client.setex(
            announcement_id,
            timedelta(days=7),
            json.dumps(announcement)
        )

        # Добавляем в список активных анонсов
        self.redis_client.sadd('active_webinar_announcements', announcement_id)

        return announcement_id

    def get_active_announcements(self) -> List[Dict[str, Any]]:
        """Получение активных оповещений для главной страницы"""
        announcement_ids = self.redis_client.smembers('active_webinar_announcements')
        announcements = []

        for ann_id in announcement_ids:
            announcement_data = self.redis_client.get(ann_id)
            if announcement_data:
                try:
                    announcement = json.loads(announcement_data)
                    announcements.append(announcement)
                except json.JSONDecodeError:
                    # Удаляем битые данные
                    self.redis_client.srem('active_webinar_announcements', ann_id)
                    self.redis_client.delete(ann_id)

        # Сортируем по дате (ближайшие первыми)
        announcements.sort(key=lambda x: x['scheduled_at'])
        return announcements

    # ==================== БАЗА ДАННЫХ УВЕДОМЛЕНИЙ ====================

    async def create_notification(
            self,
            db: AsyncSession,
            user_id: int,
            title: str,
            message: str,
            notification_type: str,
            related_entity_type: Optional[str] = None,
            related_entity_id: Optional[int] = None,
            action_url: Optional[str] = None,
            meta_data: Optional[Dict[str, Any]] = None
    ) -> models.Notification:
        """Создание уведомления с учетом настроек пользователя"""
        try:
            # Получаем настройки пользователя
            result = await db.execute(
                select(models.UserNotificationSettings).where(
                    models.UserNotificationSettings.user_id == user_id
                )
            )
            user_settings = result.scalar_one_or_none()

            # Определяем способ отправки
            send_via_email = False
            send_via_push = False
            send_via_websocket = True

            if user_settings:
                if notification_type == "webinar_reminder":
                    send_via_email = user_settings.email_webinar_reminders
                    send_via_push = user_settings.push_webinar_starting
                elif notification_type == "webinar_invite":
                    send_via_email = user_settings.email_webinar_invites
                    send_via_push = user_settings.push_webinar_starting
                elif notification_type == "new_post":
                    send_via_email = user_settings.email_project_updates
                    send_via_push = user_settings.push_new_followers
                elif notification_type == "webinar_registration_confirmation":
                    send_via_email = user_settings.email_webinar_invites
                    send_via_push = True  # Всегда показываем в платформе

            # Создаем уведомление
            notification = models.Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
                meta_data=meta_data,
                send_via_email=send_via_email,
                send_via_push=send_via_push,
                send_via_websocket=send_via_websocket,
                is_sent=not send_via_email  # Email отправляется отдельно
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            # WebSocket уведомление
            if send_via_websocket:
                from src.tasks.tasks import send_websocket_notification
                send_websocket_notification.delay(
                    user_id=user_id,
                    notification_type=notification_type,
                    data={
                        "notification_id": notification.id,
                        "title": title,
                        "message": message,
                        "action_url": action_url,
                        "meta_data": meta_data
                    }
                )

            # Email в очередь
            if send_via_email:
                await self._add_to_email_queue(db, notification)

            logger.info(f"Notification created for user {user_id}: {notification_type}")
            return notification

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise

    async def _add_to_email_queue(self, db: AsyncSession, notification: models.Notification):
        """Добавление email в очередь на отправку"""
        try:
            # Получаем пользователя
            result = await db.execute(
                select(models.User).where(models.User.id == notification.user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return

            # Получаем шаблон email
            result = await db.execute(
                select(models.NotificationTemplate).where(
                    models.NotificationTemplate.template_type == notification.notification_type,
                    models.NotificationTemplate.is_active == True
                )
            )
            template = result.scalar_one_or_none()

            # Создаем email в очереди
            email_queue = models.EmailQueue(
                user_id=user.id,
                email=user.email,
                subject=template.email_subject if template else notification.title,
                template_name=notification.notification_type,
                template_data={
                    "username": user.username,
                    "title": notification.title,
                    "message": notification.message,
                    "action_url": notification.action_url,
                    "meta_data": notification.meta_data
                },
                status="pending",
                priority=1 if notification.notification_type in ["webinar_reminder", "donation_received"] else 3
            )

            db.add(email_queue)
            await db.commit()

        except Exception as e:
            logger.error(f"Error adding to email queue: {e}")

    async def mark_as_read(self, db: AsyncSession, notification_id: int, user_id: int) -> bool:
        """Пометить уведомление как прочитанное"""
        try:
            result = await db.execute(
                select(models.Notification).where(
                    models.Notification.id == notification_id,
                    models.Notification.user_id == user_id
                )
            )
            notification = result.scalar_one_or_none()

            if notification and not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now()
                await db.commit()
                return True

            return False

        except Exception as e:
            await db.rollback()
            logger.error(f"Error marking notification as read: {e}")
            return False

    async def get_user_notifications(
            self,
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 50,
            unread_only: bool = False
    ) -> Sequence[Row[Any] | RowMapping | Any] | list[Any]:
        """Получение уведомлений пользователя"""
        try:
            query = select(models.Notification).where(
                models.Notification.user_id == user_id
            )

            if unread_only:
                query = query.where(models.Notification.is_read == False)

            query = query.order_by(models.Notification.created_at.desc())
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            notifications = result.scalars().all()

            return notifications

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []


notification_service = NotificationService()