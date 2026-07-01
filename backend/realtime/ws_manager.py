from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self._connections = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        connections = self._connections.get(session_id)
        if connections and websocket in connections:
            connections.remove(websocket)
        if connections and len(connections) == 0:
            self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: dict):
        connections = list(self._connections.get(session_id, []))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(session_id, websocket)
