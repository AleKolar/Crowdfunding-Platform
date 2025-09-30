# src/database/redis_client.py
import redis.asyncio as redis
from src.config.settings import settings
import json
from typing import Optional, Any


class RedisManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def init_redis(self):
        """Инициализация Redis подключения"""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )

        # Проверяем подключение
        try:
            await self.redis_client.ping()
            print("✅ Redis подключен успешно")
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            raise

    async def close_redis(self):
        """Закрытие Redis подключения"""
        if self.redis_client:
            await self.redis_client.close()

    async def set_key(self, key: str, value: Any, expire: int = None):
        """Установка значения"""
        if self.redis_client:
            serialized_value = json.dumps(value)
            await self.redis_client.set(key, serialized_value, ex=expire)

    async def get_key(self, key: str) -> Optional[Any]:
        """Получение значения"""
        if self.redis_client:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        return None

    async def delete_key(self, key: str):
        """Удаление ключа"""
        if self.redis_client:
            await self.redis_client.delete(key)

    async def publish(self, channel: str, message: dict):
        """Публикация в канал"""
        if self.redis_client:
            await self.redis_client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        """Подписка на канал"""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub


# Глобальный экземпляр менеджера Redis
redis_manager = RedisManager()