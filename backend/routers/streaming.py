"""Live Streaming Analysis — accepts audio/video chunks for real-time processing."""

import io
import uuid
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(prefix="/stream", tags=["Live Streaming"])


class StreamChunk(BaseModel):
    session_id: str | None = None
    modality: str  # audio or video


@router.post("/upload-chunk")
async def upload_chunk(
    modality: str = "audio",
    session_id: str | None = None,
    file: UploadFile = File(...),
):
    """Upload an audio/video chunk for real-time analysis."""
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    data = await file.read()

    if modality == "audio":
        result = await _analyze_audio_chunk(data, file.filename or "chunk.wav")
    elif modality == "video":
        result = await _analyze_video_chunk(data, file.filename or "chunk.mp4")
    else:
        return {"error": f"Unsupported modality: {modality}"}

    return {"session_id": session_id, "modality": modality, "analysis": result}


async def _analyze_audio_chunk(data: bytes, filename: str) -> dict:
    """Analyze a single audio chunk."""
    import tempfile
    from pathlib import Path

    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        from backend.services.model_loader import get_audio_model
        model = get_audio_model()
        if not model:
            return {"label": "unknown", "confidence": 0.0, "error": "Audio model not loaded"}
        return model.predict(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def _analyze_video_chunk(data: bytes, filename: str) -> dict:
    """Analyze a single video chunk."""
    import tempfile
    from pathlib import Path

    suffix = Path(filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        from backend.services.model_loader import get_video_model
        model = get_video_model()
        if not model:
            return {"label": "unknown", "confidence": 0.0, "error": "Video model not loaded"}
        return model.predict(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# --- WebSocket for real-time streaming ---
active_sessions: dict[str, list] = {}


@router.websocket("/ws/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio/video streaming."""
    await websocket.accept()
    active_sessions[session_id] = []

    try:
        while True:
            data = await websocket.receive_bytes()
            # Analyze chunk
            result = await _analyze_audio_chunk(data, "stream.wav")
            await websocket.send_json({
                "session_id": session_id,
                "analysis": result,
                "chunk_count": len(active_sessions[session_id]),
            })
            active_sessions[session_id].append(result)
    except WebSocketDisconnect:
        active_sessions.pop(session_id, None)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        active_sessions.pop(session_id, None)
