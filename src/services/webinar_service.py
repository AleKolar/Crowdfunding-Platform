import livekit
import asyncio
from datetime import datetime, timedelta


class WebinarService:
    def __init__(self):
        self.livekit_host = "http://localhost:7880"
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET

    async def create_webinar_room(self, webinar_id: int, title: str) -> str:
        """Создание комнаты для вебинара"""
        token = livekit.AccessToken(
            self.api_key,
            self.api_secret,
            identity=f"creator_{webinar_id}",
            name=title
        )

        room_grant = livekit.VideoGrant(room_create=True, room_join=True)
        token.add_grant(room_grant)

        room_name = f"webinar_{webinar_id}"
        return room_name, token.to_jwt()

    async def generate_participant_token(self, webinar_id: int, user_id: int) -> str:
        """Генерация токена для участника"""
        token = livekit.AccessToken(
            self.api_key,
            self.api_secret,
            identity=f"user_{user_id}",
            name=f"Participant {user_id}"
        )

        room_grant = livekit.VideoGrant(
            room_join=True,
            room=f"webinar_{webinar_id}",
            can_publish=False,  # Участники только смотрят
            can_subscribe=True
        )
        token.add_grant(room_grant)

        return token.to_jwt()