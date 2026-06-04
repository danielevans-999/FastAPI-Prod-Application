from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List
from app.core.security import decode_token

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """Manages all active WebSocket connections"""

    def __init__(self):
        # room_id -> list of connections
        self.rooms: Dict[str, List[WebSocket]] = {}
        # user_id -> websocket (for direct messages)
        self.users: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)
        self.users[user_id] = websocket

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
        self.users.pop(user_id, None)

    async def send_to_room(self, message: str, room_id: str):
        """Broadcast to everyone in a room"""
        if room_id in self.rooms:
            dead = []
            for connection in self.rooms[room_id]:
                try:
                    await connection.send_text(message)
                except:
                    dead.append(connection)
            for d in dead:
                self.rooms[room_id].remove(d)

    async def send_to_user(self, message: str, user_id: str):
        """Send direct message to a specific user"""
        if user_id in self.users:
            try:
                await self.users[user_id].send_text(message)
            except:
                self.users.pop(user_id, None)


manager = ConnectionManager()


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)  # pass token as query param: /ws/chat/room1?token=xxx
):
    """
    Real time chat WebSocket
    Connect: ws://localhost:8000/ws/chat/room123?token=your-jwt-token
    """
    # Authenticate via token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = payload.get("sub")
    await manager.connect(websocket, room_id, user_id)

    try:
        # Announce join
        await manager.send_to_room(
            f"User {user_id} joined room {room_id}", room_id
        )
        while True:
            # Wait for message from this client
            data = await websocket.receive_text()
            # Broadcast to everyone in room
            await manager.send_to_room(
                f"User {user_id}: {data}", room_id
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)
        await manager.send_to_room(
            f"User {user_id} left room {room_id}", room_id
        )


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    Personal notification WebSocket — one per user
    Connect: ws://localhost:8000/ws/notifications?token=your-jwt-token
    """
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = payload.get("sub")
    await websocket.accept()
    manager.users[user_id] = websocket

    try:
        while True:
            # Keep connection alive — client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.users.pop(user_id, None)
