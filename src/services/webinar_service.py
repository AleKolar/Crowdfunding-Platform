# src/services/webinar_service.py
from livekit.api import AccessToken
from livekit.api.access_token import VideoGrants
from src.config.settings import settings


class WebinarService:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET

    def create_webinar_room(self, webinar_id: int, title: str) -> tuple[str, str]:
        """Создание комнаты для вебинара"""
        room_name = f"webinar_{webinar_id}"

        # !!! Создаем объект VideoGrants для создателя, нужно Явно Все параметры !!!
        grants = VideoGrants()
        grants.room_create = True
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = True
        grants.can_subscribe = True
        grants.can_publish_data = True
        grants.room_admin=True
        grants.hidden = False
        grants.recorder = False

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"creator_{webinar_id}")
            .with_name(f"Creator - {title}")
            .with_grants(grants)
        )

        creator_token = token.to_jwt()
        return room_name, creator_token

    def generate_participant_token(self, webinar_id: int, user_id: int, username: str = None) -> str:
        """Генерация токена для участника"""
        room_name = f"webinar_{webinar_id}"
        participant_name = username or f"User {user_id}"

        # Создаем объект VideoGrants для участника
        grants = VideoGrants()
        grants.room_join = True
        grants.room = room_name
        grants.can_publish = False
        grants.can_subscribe = True
        grants.can_publish_data = False
        grants.room_admin = False
        grants.hidden = False
        grants.recorder = False

        token = (
            AccessToken(api_key=self.api_key, api_secret=self.api_secret)
            .with_identity(f"user_{user_id}")
            .with_name(participant_name)
            .with_grants(grants)
        )

        return token.to_jwt()