"""Secure Upload Sandbox.

Treats every uploaded file as untrusted input.
Full pipeline: validate → quarantine → process → cleanup.
"""

import os
import tempfile
import logging
import hashlib
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.sandbox")

# Limits
MAX_FILE_SIZE_MB = int(os.getenv("TL_MAX_FILE_MB", "100"))
MAX_VIDEO_DURATION_S = int(os.getenv("TL_MAX_VIDEO_S", "300"))
MAX_AUDIO_DURATION_S = int(os.getenv("TL_MAX_AUDIO_S", "300"))

# ponytail: in-memory quarantine. For production, persist to DB + disk quarantine folder.
_quarantine: dict[str, dict] = {}

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/flac"}
ALL_ALLOWED = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES


@dataclass
class ValidationResult:
    valid: bool
    file_type: str  # "image", "video", "audio", "unknown"
    mime_type: str
    file_size: int
    sha256: str
    errors: list[str] = None

    def to_dict(self):
        d = asdict(self)
        if d["errors"] is None:
            d["errors"] = []
        return d


def validate_upload_sandbox(
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
) -> ValidationResult:
    """Full validation pipeline for uploaded files."""
    errors = []

    # 1. Size check
    size = len(file_bytes)
    if size > MAX_FILE_SIZE_MB * 1024 * 1024:
        errors.append(f"File too large: {size / 1024 / 1024:.1f}MB (max {MAX_FILE_SIZE_MB}MB)")

    if size == 0:
        errors.append("Empty file")

    # 2. MIME verification
    mime = content_type or "application/octet-stream"
    if mime not in ALL_ALLOWED and not mime.startswith("image/") and not mime.startswith("video/") and not mime.startswith("audio/"):
        errors.append(f"Unsupported MIME type: {mime}")

    # 3. Extension validation
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    ext_to_mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".bmp": "image/bmp", ".tiff": "image/tiff",
        ".mp4": "video/mp4", ".avi": "video/avi", ".mov": "video/quicktime",
        ".webm": "video/webm", ".mkv": "video/x-matroska",
        ".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg",
        ".m4a": "audio/x-m4a", ".aac": "audio/aac", ".flac": "audio/flac",
    }
    if ext in ext_to_mime and ext_to_mime[ext] != mime:
        errors.append(f"Extension {ext} doesn't match MIME {mime}")

    # 4. Magic bytes check (basic)
    if size >= 4:
        magic_ok = _check_magic_bytes(file_bytes, mime)
        if not magic_ok:
            errors.append(f"Magic bytes don't match MIME type {mime}")

    # 5. Determine file type category
    file_type = "unknown"
    if mime.startswith("image/"):
        file_type = "image"
    elif mime.startswith("video/"):
        file_type = "video"
    elif mime.startswith("audio/"):
        file_type = "audio"

    # 6. SHA-256
    sha = hashlib.sha256(file_bytes).hexdigest()

    return ValidationResult(
        valid=len(errors) == 0,
        file_type=file_type,
        mime_type=mime,
        file_size=size,
        sha256=sha,
        errors=errors if errors else None,
    )


def _check_magic_bytes(data: bytes, mime: str) -> bool:
    """Basic magic byte check — not exhaustive but catches obvious mismatches."""
    if len(data) < 4:
        return True
    header = data[:12]
    if mime.startswith("image/jpeg") and header[:2] != b"\xff\xd8":
        return False
    if mime == "image/png" and header[:4] != b"\x89PNG":
        return False
    if mime == "image/webp" and header[8:12] != b"WEBP":
        return False
    if mime == "video/mp4" and b"ftyp" not in header[:12]:
        return False
    if mime == "audio/mpeg" and header[:2] not in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID"):
        return False
    if mime == "audio/wav" and header[:4] != b"RIFF":
        return False
    return True


def create_safe_tempdir() -> str:
    """Create a safe temporary directory for processing."""
    return tempfile.mkdtemp(prefix="truthlens_sandbox_")


def cleanup_tempdir(path: str):
    """Safely remove a temporary directory."""
    import shutil
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        logger.warning("Failed to cleanup temp dir %s: %s", path, e)


def quarantine_file(sha256: str, filename: str, reason: str, file_bytes: bytes | None = None) -> dict:
    """Move a suspicious file to quarantine."""
    import hashlib
    entry = {
        "sha256": sha256,
        "filename": filename,
        "reason": reason,
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(file_bytes) if file_bytes else 0,
        "status": "QUARANTINED",
    }
    _quarantine[sha256] = entry
    logger.warning("QUARANTINED: %s reason=%s", filename, reason)
    return entry


def get_quarantine_list() -> list[dict]:
    return list(_quarantine.values())

def release_from_quarantine(sha256: str) -> bool:
    if sha256 in _quarantine:
        _quarantine[sha256]["status"] = "RELEASED"
        return True
    return False
