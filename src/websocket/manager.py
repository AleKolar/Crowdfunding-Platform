# src/websocket/manager.py
import websockets
import redis.asyncio as redis
import json


class WebSocketManager:
    def __init__(self):
        self.connected_clients = {}
        self.redis = redis.Redis(host='redis', port=6379, db=0)

    async def handle_connection(self, websocket, user_id: int):
        """Обработка подключения WebSocket"""
        self.connected_clients[user_id] = websocket
        pubsub = None  # Инициализируем переменную

        try:
            # Подписываемся на Redis канал пользователя
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f'user_{user_id}')

            # Отправляем приветственное сообщение
            welcome_msg = {
                'type': 'connection_established',
                'message': 'WebSocket connected successfully'
            }
            await websocket.send(json.dumps(welcome_msg))

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        await websocket.send(message['data'].decode('utf-8'))
                    except websockets.exceptions.ConnectionClosed:
                        break

        except Exception as e:
            print(f"WebSocket error for user {user_id}: {e}")
        finally:
            # Всегда очищаем подключение
            if user_id in self.connected_clients:
                del self.connected_clients[user_id]
            if pubsub:
                try:
                    await pubsub.unsubscribe(f'user_{user_id}')
                    await pubsub.close()
                except Exception as e:
                    print(f"Error cleaning up pubsub: {e}")

    async def send_direct_message(self, user_id: int, message: dict):
        """Прямая отправка сообщения пользователю"""
        if user_id in self.connected_clients:
            try:
                await self.connected_clients[user_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                # Удаляем отключенного клиента
                del self.connected_clients[user_id]


manager = WebSocketManager()