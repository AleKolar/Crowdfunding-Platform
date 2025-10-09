# src/services/webinar_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from livekit.api import AccessToken
from livekit.api.access_token import VideoGrants
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import models
from src.services.template_service import template_service
from src.repository.webinar_repository import webinar_repository
from src.repository.user_repository import user_repository

logger = logging.getLogger(__name__)


class WebinarService:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET

    def create_webinar_room(self, webinar_id: int, title: str) -> tuple[str, str]:
        """Создание комнаты для вебинара"""
        room_name = f"webinar_{webinar_id}"

        grants = VideoGrants()
        grants.room_create = True
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = True
        grants.can_subscribe = True
        grants.can_publish_data = True
        grants.room_admin = True
        grants.hidden = False
        grants.recorder = False

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"creator_{webinar_id}")
            .with_name(f"Creator - {title}")
            .with_grants(grants)
            .with_ttl(timedelta(hours=3))
        )

        creator_token = token.to_jwt()
        return room_name, creator_token

    def generate_participant_token(self, webinar_id: int, user_id: int, username: str = None) -> str:
        """Генерация токена для участника"""
        room_name = f"webinar_{webinar_id}"
        participant_name = username or f"User {user_id}"

        grants = VideoGrants()
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = False
        grants.can_subscribe = True
        grants.can_publish_data = True
        grants.room_admin = False
        grants.hidden = False
        grants.recorder = False

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"user_{user_id}")
            .with_name(participant_name)
            .with_grants(grants)
            .with_ttl(timedelta(hours=3))
        )

        return token.to_jwt()

    async def register_for_webinar(self, db: AsyncSession, webinar_id: int, user_id: int) -> Dict[str, Any]:
        """СУПЕР-ПРОСТАЯ регистрация на вебинар - ОДИН КЛИК"""
        try:
            webinar = await webinar_repository.get_webinar_by_id(db, webinar_id)

            if not webinar:
                return {"success": False, "message": "Вебинар не найден"}

            if webinar.scheduled_at < datetime.now():
                return {"success": False, "message": "Вебинар уже завершился"}

            if webinar.available_slots <= 0:
                return {"success": False, "message": "Извините, все места заняты"}

            existing_registration = await webinar_repository.get_user_registration(db, webinar_id, user_id)

            if existing_registration:
                return {
                    "success": True,
                    "message": "Вы уже зарегистрированы!",
                    "already_registered": True
                }

            registration = await webinar_repository.create_registration(db, webinar_id, user_id)

            user = await user_repository.get_user_by_id(db, user_id)

            if user:
                await self._send_registration_confirmation(db, user, webinar, registration)

                # ✅ Создаем уведомление на платформе
                from src.tasks.tasks import create_platform_notification
                create_platform_notification.delay(
                    user_id=user_id,
                    title="✅ Вы зарегистрированы на вебинар!",
                    message=f'Вебинар "{webinar.title}" - {webinar.scheduled_at.strftime("%d.%m.%Y в %H:%M")}',
                    notification_type="webinar_registration"
                )

            return {
                "success": True,
                "message": "🎉 Вы успешно зарегистрированы на вебинар!",
                "registration_id": registration.id,
                "webinar_title": webinar.title,
                "scheduled_at": webinar.scheduled_at,
                "already_registered": False
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error registering for webinar: {e}")
            return {"success": False, "message": "Ошибка регистрации"}

    async def _send_registration_confirmation(self, db: AsyncSession, user: models.User, webinar: models.Webinar,
                                              registration: models.WebinarRegistration):
        """Отправка подтверждения регистрации через систему уведомлений"""
        try:
            from src.services.notification_service import notification_service

            email_content = self._create_registration_email_content(
                username=user.username,
                webinar_title=webinar.title,
                scheduled_at=webinar.scheduled_at,
                duration=webinar.duration,
                action_url=f"{settings.PLATFORM_URL}/webinars"
            )

            await notification_service.create_notification(
                db=db,
                user_id=user.id,
                title="🎉 Вы зарегистрированы на вебинар!",
                message=email_content,
                notification_type="webinar_registration_confirmation",
                related_entity_type="webinar",
                related_entity_id=webinar.id,
                action_url=f"{settings.PLATFORM_URL}/webinars",
                meta_data={
                    "webinar_title": webinar.title,
                    "scheduled_at": webinar.scheduled_at.isoformat(),
                    "registration_id": registration.id,
                    "duration": webinar.duration,
                    "room_name": f"webinar_{webinar.id}"
                }
            )

            logger.info(f"Registration confirmation notification created for user {user.id}")

        except Exception as e:
            logger.error(f"Error sending registration confirmation: {e}")

    def _create_registration_email_content(self, username: str, webinar_title: str, scheduled_at: datetime,
                                           duration: int, action_url: str) -> str:
        """Создание содержимого для email подтверждения через шаблон"""
        try:
            return template_service.render_email_template(
                "webinar_registration.html",
                username=username,
                webinar_title=webinar_title,
                scheduled_at=scheduled_at.strftime('%d.%m.%Y в %H:%M'),
                duration=duration,
                action_url=action_url
            )
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            return f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Привет, {username}!</h2>
                <p>Вы успешно зарегистрировались на вебинар:</p>
                <h3>"{webinar_title}"</h3>
                <p><strong>Дата и время:</strong> {scheduled_at.strftime('%d.%m.%Y в %H:%M')}</p>
                <p>Мы рады видеть вас на нашем вебинаре! 🚀</p>
            </div>
            """

    async def join_webinar(self, db: AsyncSession, webinar_id: int, user_id: int) -> Dict[str, Any]:
        """Присоединение к вебинару"""
        try:
            registration = await webinar_repository.get_user_registration(db, webinar_id, user_id)

            if not registration:
                return {"success": False, "message": "Вы не зарегистрированы на этот вебинар"}

            webinar = registration.webinar

            user = await user_repository.get_user_by_id(db, user_id)

            # Проверяем время вебинара (разрешаем присоединиться за 15 минут до начала)
            time_diff = (webinar.scheduled_at - datetime.now()).total_seconds()
            if time_diff > 900:  # 15 минут
                return {"success": False, "message": "Вебинар еще не начался"}

            # Генерируем токен
            participant_token = self.generate_participant_token(webinar_id, user_id, user.username if user else None)

            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ДЛЯ ОТМЕТКИ ПРИСУТСТВИЯ
            await webinar_repository.mark_attended(db, webinar_id, user_id)

            # Создаем уведомление о присоединении
            await self._create_join_notification(db, user_id, webinar)

            return {
                "success": True,
                "participant_token": participant_token,
                "room_name": f"webinar_{webinar_id}",
                "webinar_title": webinar.title
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error joining webinar: {e}")
            return {"success": False, "message": "Ошибка присоединения к вебинару"}

    async def _create_join_notification(self, db: AsyncSession, user_id: int, webinar: models.Webinar):
        """Создание уведомления о присоединении к вебинару"""
        try:
            from src.services.notification_service import notification_service

            await notification_service.create_notification(
                db=db,
                user_id=user_id,
                title="🎯 Вы присоединились к вебинару",
                message=f'Вы успешно присоединились к вебинару "{webinar.title}"',
                notification_type="webinar_joined",
                related_entity_type="webinar",
                related_entity_id=webinar.id,
                meta_data={
                    "webinar_title": webinar.title,
                    "joined_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error creating join notification: {e}")


webinar_service = WebinarService()