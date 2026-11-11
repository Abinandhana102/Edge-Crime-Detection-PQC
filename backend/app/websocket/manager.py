"""
WebSocket Alert & Telemetry Broadcast Manager
Maintains live connections to Police Dashboards and broadcasts real-time alerts.
"""

import json
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages active WebSocket connections from police command clients"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcasts real-time critical crime / intrusion / weapon alert to all connected dashboards"""
        message = {
            "type": "CRITICAL_ALERT",
            "data": alert_data
        }
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def broadcast_telemetry(self, telemetry_data: Dict[str, Any]):
        """Broadcasts AI detection bounding boxes, FPS, and status updates"""
        message = {
            "type": "AI_TELEMETRY",
            "data": telemetry_data
        }
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()
