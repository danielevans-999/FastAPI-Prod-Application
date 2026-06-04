from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for:
    - Private messaging (user to user)
    - Room based chat
    - Real time notifications
    - Live dashboard updates
    """

    def __init__(self):
        # user_id → list of their websocket connections
        self.user_connections: Dict[int, List[WebSocket]] = {}

        # room_id → set of user_ids in that room
        self.rooms: Dict[str, Set[int]] = {}

        # all active connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        logger.info(f"User {user_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                ws for ws in self.user_connections[user_id] if ws != websocket
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # remove from all rooms
        for room_id in list(self.rooms.keys()):
            self.rooms[room_id].discard(user_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

        logger.info(f"User {user_id} disconnected. Total: {len(self.active_connections)}")

    async def join_room(self, room_id: str, user_id: int):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(user_id)
        logger.info(f"User {user_id} joined room {room_id}")

    async def leave_room(self, room_id: str, user_id: int):
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user (all their connections)"""
        if user_id in self.user_connections:
            dead_connections = []
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    dead_connections.append(websocket)

            # clean up dead connections
            for ws in dead_connections:
                self.disconnect(ws, user_id)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: int = None):
        """Broadcast message to everyone in a room"""
        if room_id not in self.rooms:
            return

        for user_id in self.rooms[room_id]:
            if user_id != exclude_user:
                await self.send_to_user(user_id, message)

    async def broadcast_to_all(self, message: dict):
        """Broadcast to every connected user"""
        dead_connections = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        for ws in dead_connections:
            self.active_connections.remove(ws)

    def get_online_users(self) -> List[int]:
        """Returns list of currently connected user IDs"""
        return list(self.user_connections.keys())

    def is_user_online(self, user_id: int) -> bool:
        return user_id in self.user_connections


# Single global instance
manager = ConnectionManager()
