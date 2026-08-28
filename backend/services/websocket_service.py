"""WebSocket Real-Time Updates.

Allows clients to subscribe to analysis progress via WebSocket.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.websocket")

# Active connections: analysis_id → [websocket]
_connections: dict[str, list] = {}
# Progress store: analysis_id → progress_dict
_progress: dict[str, dict] = {}


async def connect(analysis_id: str, websocket):
    """Register a WebSocket connection for an analysis."""
    await websocket.accept()
    _connections.setdefault(analysis_id, []).append(websocket)
    logger.info("WS connected: %s", analysis_id)
    # Send current progress if available
    if analysis_id in _progress:
        await websocket.send_json(_progress[analysis_id])


async def disconnect(analysis_id: str, websocket):
    """Remove a WebSocket connection."""
    if analysis_id in _connections:
        _connections[analysis_id] = [ws for ws in _connections[analysis_id] if ws != websocket]
        if not _connections[analysis_id]:
            del _connections[analysis_id]


async def broadcast_progress(analysis_id: str, progress: dict):
    """Broadcast progress to all connected clients."""
    _progress[analysis_id] = progress
    if analysis_id in _connections:
        dead = []
        for ws in _connections[analysis_id]:
            try:
                await ws.send_json(progress)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _connections[analysis_id].remove(ws)


def update_progress(analysis_id: str, module: str, status: str, pct: float = 0):
    """Update progress for a module."""
    if analysis_id not in _progress:
        _progress[analysis_id] = {"analysis_id": analysis_id, "modules": {}, "overall_pct": 0}
    _progress[analysis_id]["modules"][module] = {"status": status, "pct": pct}
    modules = _progress[analysis_id]["modules"]
    _progress[analysis_id]["overall_pct"] = round(
        sum(m.get("pct", 0) for m in modules.values()) / max(len(modules), 1), 1
    )
    # Fire and forget broadcast
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_progress(analysis_id, _progress[analysis_id]))
    except RuntimeError:
        pass


def get_progress(analysis_id: str) -> dict | None:
    return _progress.get(analysis_id)
