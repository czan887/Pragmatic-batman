"""
WebSocket routes for real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio
import json
from datetime import datetime
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates

    Supports multiple connection types:
    - logs: Real-time log streaming
    - tasks: Task queue updates
    - profiles: Profile status updates
    """

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {
            "logs": [],
            "tasks": [],
            "profiles": [],
            "all": []  # Receives all updates
        }
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str = "logs"):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)
            self.active_connections["all"].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str = "logs"):
        """Remove a WebSocket connection"""
        async with self._lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)
            if websocket in self.active_connections["all"]:
                self.active_connections["all"].remove(websocket)

    async def broadcast(self, message: dict, channel: str = "logs"):
        """Broadcast message to all connections in a channel"""
        connections = self.active_connections.get(channel, [])
        dead_connections = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"WebSocket connection dead on channel '{channel}': {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        if dead_connections:
            logger.debug(f"Cleaning up {len(dead_connections)} dead WebSocket connection(s) from '{channel}'")
        for conn in dead_connections:
            await self.disconnect(conn, channel)

    async def broadcast_log(self, level: str, message: str, profile_id: Optional[str] = None):
        """Broadcast a log entry"""
        log_entry = {
            "type": "log",
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "profile_id": profile_id
        }
        await self.broadcast(log_entry, "logs")
        await self.broadcast(log_entry, "all")

    async def broadcast_task_update(self, task_id: int, status: str, data: dict = None):
        """Broadcast a task status update"""
        update = {
            "type": "task_update",
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "status": status,
            "data": data or {}
        }
        await self.broadcast(update, "tasks")
        await self.broadcast(update, "all")

    async def broadcast_profile_update(self, profile_id: str, status: str, data: dict = None):
        """Broadcast a profile status update"""
        update = {
            "type": "profile_update",
            "timestamp": datetime.now().isoformat(),
            "profile_id": profile_id,
            "status": status,
            "data": data or {}
        }
        await self.broadcast(update, "profiles")
        await self.broadcast(update, "all")

    async def broadcast_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        error_code: Optional[str] = None
    ):
        """
        Broadcast a system notification for toast display

        Args:
            notification_type: "error" | "success" | "warning" | "info"
            title: Short title for the notification
            message: Detailed message
            error_code: Optional error code for error notifications
        """
        notification = {
            "type": "notification",
            "timestamp": datetime.now().isoformat(),
            "notification_type": notification_type,
            "title": title,
            "message": message,
        }
        if error_code:
            notification["error_code"] = error_code

        # Broadcast to all channels so frontend can catch it
        await self.broadcast(notification, "logs")
        await self.broadcast(notification, "all")

    def get_connection_count(self, channel: str = None) -> int:
        """Get number of active connections"""
        if channel:
            return len(self.active_connections.get(channel, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get the connection manager instance"""
    return manager


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming

    Receives log entries as they're generated by bot operations.
    """
    await manager.connect(websocket, "logs")
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            # Handle ping/pong or other client messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "logs")


@router.websocket("/tasks")
async def websocket_tasks(websocket: WebSocket):
    """
    WebSocket endpoint for task queue updates

    Receives updates when tasks are created, started, or completed.
    """
    await manager.connect(websocket, "tasks")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "tasks")


@router.websocket("/profiles")
async def websocket_profiles(websocket: WebSocket):
    """
    WebSocket endpoint for profile status updates

    Receives updates when profile browsers are opened/closed.
    """
    await manager.connect(websocket, "profiles")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "profiles")


@router.websocket("/all")
async def websocket_all(websocket: WebSocket):
    """
    WebSocket endpoint for all updates

    Receives all types of updates (logs, tasks, profiles).
    """
    await manager.connect(websocket, "all")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "all")


@router.get("/status")
async def websocket_status():
    """
    Get WebSocket connection status

    Returns the number of active connections per channel.
    """
    return {
        "connections": {
            channel: len(connections)
            for channel, connections in manager.active_connections.items()
        }
    }


@router.post("/test-log")
async def test_log(message: str = "Test log message", level: str = "INFO"):
    """
    Send a test log message via WebSocket

    For testing purposes only.
    """
    await manager.broadcast_log(level, message, None)
    return {"status": "sent", "message": message, "level": level}


# Helper function for services to broadcast logs
async def broadcast_log(level: str, message: str, profile_id: Optional[str] = None):
    """Helper to broadcast log from anywhere in the application"""
    await manager.broadcast_log(level, message, profile_id)


# Helper function for services to broadcast notifications
async def broadcast_notification(
    notification_type: str,
    title: str,
    message: str,
    error_code: Optional[str] = None
):
    """
    Helper to broadcast notification from anywhere in the application

    Args:
        notification_type: "error" | "success" | "warning" | "info"
        title: Short title for the notification
        message: Detailed message
        error_code: Optional error code for error notifications
    """
    await manager.broadcast_notification(notification_type, title, message, error_code)
