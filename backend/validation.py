"""Shared input validation — max sizes, text limits."""

from fastapi import UploadFile, HTTPException

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_TEXT_LENGTH = 10000  # characters
MAX_BATCH_ITEMS = 20


async def validate_upload(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES):
    """Read file and enforce size limit. Raises400 if too large."""
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(contents)} bytes (max {max_bytes})",
        )
    return contents


def validate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """Validate text input length. Raises400 if too long."""
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long: {len(text)} chars (max {max_length})",
        )
    return text.strip()
