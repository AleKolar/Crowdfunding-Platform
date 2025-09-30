# src/utils/redis_utils.py
from src.database.redis_client import redis_manager
from typing import Optional, Any
import json

async def cache_get(key: str) -> Optional[Any]:
    """Получение данных из кэша"""
    return await redis_manager.get_key(key)

async def cache_set(key: str, value: Any, expire: int = 3600):
    """Сохранение данных в кэш"""
    await redis_manager.set_key(key, value, expire)

async def cache_delete(key: str):
    """Удаление данных из кэша"""
    await redis_manager.delete_key(key)

async def get_online_users() -> list:
    """Получение списка онлайн пользователей"""
    try:
        online_users = await redis_manager.get_key("online_users")
        return online_users or []
    except:
        return []

async def add_online_user(user_id: int):
    """Добавление пользователя в список онлайн"""
    try:
        online_users = await get_online_users()
        if user_id not in online_users:
            online_users.append(user_id)
            await redis_manager.set_key("online_users", online_users, expire=3600)
    except:
        pass

async def remove_online_user(user_id: int):
    """Удаление пользователя из списка онлайн"""
    try:
        online_users = await get_online_users()
        if user_id in online_users:
            online_users.remove(user_id)
            await redis_manager.set_key("online_users", online_users, expire=3600)
    except:
        pass