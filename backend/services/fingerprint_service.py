"""Media Fingerprint — creates unique identity for uploaded content. ponytail: hashlib stdlib."""

import hashlib


def generate_media_id(sha256: str) -> str:
    """TL-M-XXXX-XXXX from first 16 hex chars of SHA-256."""
    h = sha256[:16].upper()
    return f"TL-M-{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def create_fingerprint(data: bytes, filename: str, content_type: str, analysis_id: str | None = None) -> dict:
    """Create a media fingerprint record."""
    from backend.db.database import async_session
    from backend.db.models_advanced import MediaFingerprint
    from sqlalchemy import select

    sha256 = hash_bytes(data)
    media_id = generate_media_id(sha256)

    async with async_session() as session:
        # Check if already exists
        existing = await session.execute(select(MediaFingerprint).where(MediaFingerprint.sha256 == sha256))
        if existing := existing.scalar_one_or_none():
            return {"media_id": existing.media_id, "sha256": sha256, "duplicate": True}

        fp = MediaFingerprint(
            media_id=media_id, sha256=sha256,
            file_size=len(data), file_type=content_type,
            filename=filename, analysis_id=analysis_id,
        )
        session.add(fp)
        await session.commit()
        return {"media_id": media_id, "sha256": sha256, "duplicate": False}


async def lookup_by_hash(sha256: str) -> dict | None:
    from backend.db.database import async_session
    from backend.db.models_advanced import MediaFingerprint
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(MediaFingerprint).where(MediaFingerprint.sha256 == sha256))
        fp = result.scalar_one_or_none()
        if not fp:
            return None
        return {"media_id": fp.media_id, "sha256": fp.sha256, "file_size": fp.file_size, "file_type": fp.file_type, "filename": fp.filename, "created_at": fp.created_at.isoformat()}
