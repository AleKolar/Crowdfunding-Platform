# src/websocket/handler.py
import asyncio
import websockets
from src.websocket.manager import manager
from src.websocket.auth import authenticate_websocket


async def websocket_handler(websocket) -> None:
    """Обработчик WebSocket соединений"""
    try:
        # Путь из websocket объекта
        path = websocket.path
        query_string = path.split('?')[-1] if '?' in path else ""
        query_params = {}

        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value

        token = query_params.get('token', '')

        if not token:
            await websocket.close(1008, "Authentication required")
            return

        user_id = await authenticate_websocket(token)

        if not user_id:
            await websocket.close(1008, "Invalid token")
            return

        print(f"User {user_id} connected via WebSocket")
        await manager.handle_connection(websocket, user_id)

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed normally")
    except Exception as e:
        print(f"WebSocket handler error: {e}")
        try:
            await websocket.close(1011, "Internal server error")
        except:
            pass


async def start_websocket_server():
    """Запуск WebSocket сервера"""
    from src.config.settings import settings

    server = await websockets.serve(
        websocket_handler,
        "0.0.0.0",
        settings.WEBSOCKET_PORT
    )

    print(f"WebSocket server started on port {settings.WEBSOCKET_PORT}")
    return server