# src/services/webinar_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from livekit.api import AccessToken
from livekit.api.access_token import VideoGrants
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import models

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
        grants.can_publish_data = True  # Разрешаем чат
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
            # Проверяем существование вебинара
            result = await db.execute(
                select(models.Webinar).where(
                    models.Webinar.id == webinar_id,
                    models.Webinar.status == "scheduled"
                )
            )
            webinar = result.scalar_one_or_none()

            if not webinar:
                return {"success": False, "message": "Вебинар не найден"}

            # Проверяем, не прошел ли уже вебинар
            if webinar.scheduled_at < datetime.now():
                return {"success": False, "message": "Вебинар уже завершился"}

            # Проверяем свободные места
            if webinar.available_slots <= 0:
                return {"success": False, "message": "Извините, все места заняты"}

            # Проверяем, не зарегистрирован ли уже пользователь
            result = await db.execute(
                select(models.WebinarRegistration).where(
                    models.WebinarRegistration.webinar_id == webinar_id,
                    models.WebinarRegistration.user_id == user_id
                )
            )
            existing_registration = result.scalar_one_or_none()

            if existing_registration:
                return {
                    "success": True,
                    "message": "Вы уже зарегистрированы!",
                    "already_registered": True
                }

            # ✅ ПРОСТОЕ РЕШЕНИЕ: Регистрация в один клик!
            registration = models.WebinarRegistration(
                user_id=user_id,
                webinar_id=webinar_id
            )

            db.add(registration)
            await db.commit()
            await db.refresh(registration)

            # Получаем данные пользователя
            result = await db.execute(
                select(models.User).where(models.User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # ✅ Отправляем простое email подтверждение
                from src.tasks.tasks import send_webinar_registration_confirmation
                send_webinar_registration_confirmation.delay(
                    user.email,
                    user.username,
                    webinar.title,
                    webinar.scheduled_at
                )

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

    async def join_webinar(self, db: AsyncSession, webinar_id: int, user_id: int) -> Dict[str, Any]:
        """Присоединение к вебинару"""
        try:
            # Проверяем регистрацию
            result = await db.execute(
                select(models.WebinarRegistration).where(
                    models.WebinarRegistration.webinar_id == webinar_id,
                    models.WebinarRegistration.user_id == user_id
                )
            )
            registration = result.scalar_one_or_none()

            if not registration:
                return {"success": False, "message": "Вы не зарегистрированы на этот вебинар"}

            webinar = registration.webinar
            user = registration.user

            # Проверяем время вебинара (разрешаем присоединиться за 15 минут до начала)
            time_diff = (webinar.scheduled_at - datetime.now()).total_seconds()
            if time_diff > 900:  # 15 минут
                return {"success": False, "message": "Вебинар еще не начался"}

            # Генерируем токен
            participant_token = self.generate_participant_token(webinar_id, user_id, user.username)

            # Помечаем как присутствующего
            registration.attended = True
            await db.commit()

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


webinar_service = WebinarService()