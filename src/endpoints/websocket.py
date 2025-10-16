# src/endpoints/websocket.py
from fastapi import WebSocket, WebSocketDisconnect


from src.websocket.auth import authenticate_websocket
from fastapi import APIRouter

from src.websocket.handler import manager

projects_web_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_web_router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    user_id = await authenticate_websocket(token)
    if not user_id:
        await websocket.close(code=1008)
        return

    await manager.handle_connection(websocket, user_id)