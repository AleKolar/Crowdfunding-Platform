# src/websocket/manager.py
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
import redis.asyncio as redis
import json
from typing import Dict


class WebSocketManager:
    def __init__(self):
        self.connected_clients: Dict[int, WebSocketServerProtocol] = {}
        self.redis = redis.Redis(host='redis', port=6379, db=0)

    async def handle_connection(self, websocket: WebSocketServerProtocol, user_id: int) -> None:
        """Обработка подключения WebSocket"""
        self.connected_clients[user_id] = websocket
        pubsub = self.redis.pubsub()

        try:
            # Подписываемся на Redis канал пользователя
            await pubsub.subscribe(f'user_{user_id}')

            # Отправляем приветственное сообщение
            welcome_msg = {
                'type': 'connection_established',
                'message': 'WebSocket connected successfully',
                'user_id': user_id
            }
            await websocket.send(json.dumps(welcome_msg))

            # Обрабатываем сообщения из Redis
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        if isinstance(message['data'], bytes):
                            data = message['data'].decode('utf-8')
                        else:
                            data = str(message['data'])
                        await websocket.send(data)
                    except ConnectionClosed:
                        print(f"Connection closed for user {user_id}")
                        break
                    except Exception as e:
                        print(f"Error sending message to user {user_id}: {e}")
                        break

        except Exception as e:
            print(f"WebSocket error for user {user_id}: {e}")
        finally:
            # Всегда очищаем подключение
            if user_id in self.connected_clients:
                del self.connected_clients[user_id]
            try:
                await pubsub.unsubscribe(f'user_{user_id}')
                await pubsub.close()
            except Exception as e:
                print(f"Error cleaning up pubsub: {e}")

    async def send_direct_message(self, user_id: int, message: dict) -> bool:
        """Прямая отправка сообщения пользователю"""
        if user_id in self.connected_clients:
            try:
                await self.connected_clients[user_id].send(json.dumps(message))
                return True
            except ConnectionClosed:
                del self.connected_clients[user_id]
            except Exception as e:
                print(f"Error sending direct message to user {user_id}: {e}")
        return False


manager = WebSocketManager()