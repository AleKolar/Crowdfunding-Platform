# src/services/webinar_service.py
from src.services.notification_service import notification_service
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database import models
from src.services.notification_service import notification_service
from src.services.template_service import template_service
from src.repository.webinar_repository import webinar_repository
from src.repository.user_repository import user_repository

logger = logging.getLogger(__name__)

try:
    from livekit.api import AccessToken
    from livekit.api.access_token import VideoGrants

    LIVEKIT_AVAILABLE = True
    logger.info("✅ LiveKit successfully imported")
except ImportError:
    logger.warning("LiveKit not available, using mock implementation")
    from src.services.mocks.livekit_mock import AccessToken, VideoGrants

    LIVEKIT_AVAILABLE = False


class WebinarService:
    def __init__(self):
        if LIVEKIT_AVAILABLE:
            self.api_key = settings.LIVEKIT_API_KEY
            self.api_secret = settings.LIVEKIT_API_SECRET
            logger.info("LiveKit configured with API key")
        else:
            self.api_key = "mock_api_key"
            self.api_secret = "mock_api_secret"
            logger.info("Using mock LiveKit implementation")

    def _create_livekit_room(self, webinar_id: int, title: str) -> tuple[str, str]:
        """Создание комнаты LiveKit и токена для создателя"""
        room_name = f"webinar_{webinar_id}"

        grants = VideoGrants()
        grants.room_create = True
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = True  # Создатель может публиковать
        grants.can_subscribe = True
        grants.can_publish_data = True
        grants.room_admin = True  # Администратор комнаты
        grants.hidden = False

        # Дополнительные права для создателя
        try:
            grants.recorder = True  # Может записывать вебинар
        except AttributeError:
            logger.debug("recorder attribute not available")

        logger.info(f"🎯 Creating LiveKit room: {room_name} for webinar {webinar_id}")

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"creator_{webinar_id}")
            .with_name(f"Creator - {title}")
            .with_grants(grants)
            .with_ttl(timedelta(hours=3))
        )

        creator_token = token.to_jwt()
        logger.info(f"✅ LiveKit room '{room_name}' created successfully")
        return room_name, creator_token

    def generate_participant_token(self, webinar_id: int, user_id: int, username: str = None,
                                   can_publish: bool = True) -> str:
        """Генерация токена для участника

        Args:
            webinar_id: ID вебинара
            user_id: ID пользователя
            username: Имя пользователя (опционально)
            can_publish: Может ли участник публиковать видео/аудио (по умолчанию ДА)
        """
        room_name = f"webinar_{webinar_id}"
        participant_name = username or f"User {user_id}"

        grants = VideoGrants()
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = can_publish  # Участники МОГУТ публиковать по умолчанию
        grants.can_subscribe = True
        grants.can_publish_data = True  # Могут отправлять сообщения в чат
        grants.room_admin = False  # Не администраторы
        grants.hidden = False

        logger.debug(
            f"🎫 Generating participant token for user {user_id} in room '{room_name}' (can_publish={can_publish})")

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"user_{user_id}")
            .with_name(participant_name)
            .with_grants(grants)
            .with_ttl(timedelta(hours=3))
        )

        return token.to_jwt()

    def generate_creator_token(self, webinar_id: int, creator_id: int, title: str) -> str:
        """Генерация токена для создателя вебинара (администратора)"""
        room_name = f"webinar_{webinar_id}"

        grants = VideoGrants()
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = True  # Может публиковать
        grants.can_subscribe = True
        grants.can_publish_data = True
        grants.room_admin = True  # Администраторские права
        grants.hidden = False

        # Максимальные права для создателя
        try:
            grants.room_create = True  # Может создавать комнаты
            grants.recorder = True  # Может записывать
        except AttributeError:
            logger.debug("Some admin attributes not available")

        logger.info(f"👑 Generating creator token for user {creator_id} in room '{room_name}'")

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"creator_{creator_id}")
            .with_name(f"Creator - {title}")
            .with_grants(grants)
            .with_ttl(timedelta(hours=3))
        )

        return token.to_jwt()

    async def create_webinar(
            self,
            db: AsyncSession,
            creator_id: int,
            title: str,
            description: str,
            scheduled_at: datetime,
            duration: int = 60,
            max_participants: int = 100,
            is_public: bool = True,
            meta_data: Optional[Dict[str, Any]] = None
    ) -> models.Webinar:
        """Создание вебинара с автоматическим созданием комнаты LiveKit"""
        try:
            # 1. СОЗДАЕМ КОМНАТУ LIVEKIT ПЕРВОЙ
            logger.info(f"🚀 Starting webinar creation: '{title}' by user {creator_id}")

            # Временно создаем вебинар для получения ID
            webinar = models.Webinar(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                duration=duration,
                max_participants=max_participants,
                creator_id=creator_id,
                is_public=is_public,
                meta_data=meta_data or {}
            )

            db.add(webinar)
            await db.flush()  # Получаем ID без коммита
            logger.info(f"📝 Webinar record created with ID: {webinar.id}")

            # 2. СОЗДАЕМ КОМНАТУ LIVEKIT
            try:
                room_name, creator_token = self._create_livekit_room(webinar.id, title)

                # Сохраняем информацию о комнате в meta_data
                webinar.meta_data = {
                    **(webinar.meta_data or {}),
                    'livekit_room': room_name,
                    'creator_token': creator_token,  # Сохраняем токен создателя
                    'room_created_at': datetime.now().isoformat(),
                    'livekit_available': True
                }

                logger.info(f"✅ LiveKit room '{room_name}' created for webinar {webinar.id}")

            except Exception as e:
                logger.error(f"❌ Failed to create LiveKit room for webinar {webinar.id}: {e}")
                # Сохраняем информацию об ошибке
                webinar.meta_data = {
                    **(webinar.meta_data or {}),
                    'livekit_error': str(e),
                    'livekit_available': False,
                    'room_created_at': datetime.now().isoformat()
                }
                # Не прерываем создание вебинара из-за ошибки LiveKit

            # 3. ФИНАЛИЗИРУЕМ СОЗДАНИЕ ВЕБИНАРА
            await db.commit()
            await db.refresh(webinar)

            # 4. СОЗДАЕМ АНОНС В REDIS
            announcement_data = {
                'id': webinar.id,
                'title': webinar.title,
                'description': webinar.description,
                'scheduled_at': webinar.scheduled_at.isoformat(),
                'duration': webinar.duration,
                'max_participants': webinar.max_participants,
                'creator_id': webinar.creator_id,
                'livekit_room': webinar.meta_data.get('livekit_room', ''),
                'livekit_available': webinar.meta_data.get('livekit_available', False)
            }

            notification_service.create_webinar_announcement(announcement_data)

            logger.info(f"🎉 Webinar fully created: {webinar.id} by user {creator_id}")
            logger.info(f"   - Room: {webinar.meta_data.get('livekit_room', 'NOT_CREATED')}")
            logger.info(f"   - LiveKit available: {webinar.meta_data.get('livekit_available', False)}")

            return webinar

        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Error creating webinar: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create webinar: {str(e)}"
            )

    async def update_webinar(
            self,
            db: AsyncSession,
            webinar_id: int,
            updater_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[models.Webinar]:
        """Обновление вебинара с проверкой прав"""
        try:
            logger.info(f"🔄 Updating webinar {webinar_id} by user {updater_id}")

            # Получаем вебинар
            result = await db.execute(
                select(models.Webinar).where(models.Webinar.id == webinar_id)
            )
            webinar = result.scalar_one_or_none()

            if not webinar:
                logger.warning(f"Webinar {webinar_id} not found for update")
                return None

            # Проверяем права (только создатель или админ может редактировать)
            result = await db.execute(
                select(models.User).where(models.User.id == updater_id)
            )
            user = result.scalar_one_or_none()

            can_edit = (
                    webinar.creator_id == updater_id or
                    "admin" in getattr(user, 'roles', [])
            )

            if not can_edit:
                logger.warning(f"User {updater_id} doesn't have permission to edit webinar {webinar_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to edit this webinar"
                )

            # Обновляем данные
            for field, value in update_data.items():
                if hasattr(webinar, field):
                    setattr(webinar, field, value)
                    logger.debug(f"Updated field {field} for webinar {webinar_id}")

            webinar.updated_at = datetime.now()
            await db.commit()
            await db.refresh(webinar)

            # Обновляем анонс в Redis
            announcement_data = {
                'id': webinar.id,
                'title': webinar.title,
                'description': webinar.description,
                'scheduled_at': webinar.scheduled_at.isoformat(),
                'duration': webinar.duration,
                'max_participants': webinar.max_participants,
                'creator_id': webinar.creator_id,
                'livekit_room': webinar.meta_data.get('livekit_room', ''),
                'livekit_available': webinar.meta_data.get('livekit_available', False)
            }

            # Удаляем старый анонс и создаем новый
            notification_service.redis_client.delete(f"webinar_announcement_{webinar.id}")
            notification_service.redis_client.srem('active_webinar_announcements', f"webinar_announcement_{webinar.id}")

            notification_service.create_webinar_announcement(announcement_data)

            logger.info(f"✅ Webinar {webinar_id} updated successfully")
            return webinar

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating webinar {webinar_id}: {e}")
            raise

    async def send_webinar_invitations(
            self,
            db: AsyncSession,
            webinar_id: int,
            user_ids: List[int]
    ) -> int:
        """Отправка приглашений на вебинар"""
        try:
            # Получаем вебинар
            result = await db.execute(
                select(models.Webinar).where(models.Webinar.id == webinar_id)
            )
            webinar = result.scalar_one_or_none()

            if not webinar:
                return 0

            sent_count = 0
            for user_id in user_ids:
                try:
                    await notification_service.create_notification(
                        db=db,
                        user_id=user_id,
                        title=f"Приглашение на вебинар: {webinar.title}",
                        message=f"Вы приглашены на вебинар: {webinar.description}",
                        notification_type="webinar_invite",
                        related_entity_type="webinar",
                        related_entity_id=webinar.id,
                        action_url=f"/webinars/{webinar.id}",
                        meta_data={
                            "webinar_id": webinar.id,
                            "scheduled_at": webinar.scheduled_at.isoformat(),
                            "duration": webinar.duration
                        }
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending invitation to user {user_id}: {e}")
                    continue

            logger.info(f"Sent {sent_count} webinar invitations for webinar {webinar_id}")
            return sent_count

        except Exception as e:
            logger.error(f"Error sending webinar invitations: {e}")
            raise

    async def register_for_webinar(self, db: AsyncSession, webinar_id: int, user_id: int) -> Dict[str, Any]:
        """ПРОСТАЯ регистрация на вебинар в ОДИН КЛИК"""
        try:
            webinar = await webinar_repository.get_webinar_by_id(db, webinar_id)

            if not webinar:
                return {"success": False, "message": "Вебинар не найден"}

            if webinar.scheduled_at < datetime.now():
                return {"success": False, "message": "Вебинар уже завершился"}

            # Метод для проверки доступных слотов
            registrations_count = await webinar_repository.get_webinar_registrations_count(db, webinar_id)
            if registrations_count >= webinar.max_participants:
                return {"success": False, "message": "Извините, все места заняты"}

            existing_registration = await webinar_repository.get_user_registration(db, webinar_id, user_id)

            if existing_registration:
                return {
                    "success": True,
                    "message": "Вы уже зарегистрированы!",
                    "already_registered": True,
                    "webinar_id": webinar_id,
                    "webinar_title": webinar.title
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
                "webinar_id": webinar_id,
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
                    "duration": webinar.duration
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

    async def join_webinar(self, db: AsyncSession, webinar_id: int, user_id: int, is_creator: bool = False) -> Dict[
        str, Any]:
        """Присоединение к вебинару

        Args:
            is_creator: Если True - генерирует токен создателя
        """
        try:
            registration = await webinar_repository.get_user_registration(db, webinar_id, user_id)

            if not registration and not is_creator:
                return {"success": False, "message": "Вы не зарегистрированы на этот вебинар"}

            webinar = await webinar_repository.get_webinar_by_id(db, webinar_id)
            if not webinar:
                return {"success": False, "message": "Вебинар не найден"}

            user = await user_repository.get_user_by_id(db, user_id)

            # Проверяем время вебинара (разрешаем присоединиться за 15 минут до начала)
            time_diff = (webinar.scheduled_at - datetime.now()).total_seconds()
            if time_diff > 900 and not is_creator:  # 15 минут
                return {"success": False, "message": "Вебинар еще не начался"}

            # Генерируем токен в зависимости от роли
            if is_creator:
                # Создатель получает администраторские права
                participant_token = self.generate_creator_token(webinar_id, user_id, webinar.title)
                role = "creator"
            else:
                # Участники получают стандартные права (могут публиковать)
                participant_token = self.generate_participant_token(
                    webinar_id,
                    user_id,
                    user.username if user else None,
                    can_publish=True  # Участники МОГУТ публиковать по умолчанию
                )
                role = "participant"

            # Отмечаем присутствие (если не создатель)
            if not is_creator:
                await webinar_repository.mark_attended(db, webinar_id, user_id)

            # Создаем уведомление о присоединении
            await self._create_join_notification(db, user_id, webinar, role)

            return {
                "success": True,
                "token": participant_token,
                "join_url": f"{settings.PLATFORM_URL}/webinars/{webinar_id}/room",
                "message": "Вы успешно присоединились к вебинару!",
                "webinar_title": webinar.title,
                "role": role,
                "can_publish": True  # Все участники могут публиковать
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error joining webinar: {e}")
            return {"success": False, "message": "Ошибка присоединения к вебинару"}

    async def _create_join_notification(self, db: AsyncSession, user_id: int, webinar: models.Webinar, role: str):
        """Создание уведомления о присоединении к вебинару"""
        try:
            from src.services.notification_service import notification_service

            role_text = "создателем" if role == "creator" else "участником"

            await notification_service.create_notification(
                db=db,
                user_id=user_id,
                title="🎯 Вы присоединились к вебинару",
                message=f'Вы успешно присоединились к вебинару "{webinar.title}" как {role_text}',
                notification_type="webinar_joined",
                related_entity_type="webinar",
                related_entity_id=webinar.id,
                meta_data={
                    "webinar_title": webinar.title,
                    "joined_at": datetime.now().isoformat(),
                    "role": role
                }
            )

        except Exception as e:
            logger.error(f"Error creating join notification: {e}")

    async def get_webinar_room_info(self, webinar_id: int) -> Dict[str, Any]:
        """Получение информации о комнате вебинара"""
        try:
            return {
                "webinar_id": webinar_id,
                "room_name": f"webinar_{webinar_id}",
                "livekit_available": LIVEKIT_AVAILABLE
            }
        except Exception as e:
            logger.error(f"Error getting webinar room info: {e}")
            return {
                "webinar_id": webinar_id,
                "error": str(e)
            }


webinar_service = WebinarService()