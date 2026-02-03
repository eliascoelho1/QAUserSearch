"""WebSocket package for real-time communication."""

from src.api.v1.websocket.connection_manager import ConnectionManager
from src.api.v1.websocket.interpreter_ws import router as interpreter_ws_router

__all__ = ["ConnectionManager", "interpreter_ws_router"]
