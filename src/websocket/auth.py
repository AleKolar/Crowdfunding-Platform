# src/websocket/auth.py
from typing import Optional

from jose import JWTError, jwt
from src.config.settings import settings


async def authenticate_websocket(token: str) -> Optional[int]:
    """Аутентификация WebSocket соединения"""
    try:
        if not token or token == "undefined":
            return None

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None