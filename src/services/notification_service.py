# src/services/notification_service.py
import redis
import json
from datetime import timedelta
from typing import List, Dict, Any
from src.config.settings import settings


class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

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


notification_service = NotificationService()