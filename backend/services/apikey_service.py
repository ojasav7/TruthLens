"""API Key Service — authentication + per-key rate limiting."""

import hashlib
import secrets
from datetime import datetime, timezone


def generate_api_key() -> str:
    """Generate a new API key: tl_live_xxxxxxxxxxxx."""
    return f"tl_live_{secrets.token_hex(24)}"


def hash_key(key: str) -> str:
    """SHA-256 hash for storage (never store raw keys)."""
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(name: str, org_id: str | None = None, rate_limit: int = 100) -> dict:
    """Create a new API key."""
    from backend.db.database import async_session
    from backend.db.models_advanced import APIKey
    from sqlalchemy import select

    raw_key = generate_api_key()
    key_hash = hash_key(raw_key)

    async with async_session() as session:
        ak = APIKey(name=name, key_hash=key_hash, org_id=org_id, rate_limit=rate_limit)
        session.add(ak)
        await session.commit()
        return {"api_key": raw_key, "name": name, "rate_limit": rate_limit, "message": "Save this key — it won't be shown again"}


async def validate_api_key(raw_key: str) -> dict | None:
    """Validate an API key. Returns key info or None."""
    from backend.db.database import async_session
    from backend.db.models_advanced import APIKey
    from sqlalchemy import select

    key_hash = hash_key(raw_key)
    async with async_session() as session:
        result = await session.execute(select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True))
        ak = result.scalar_one_or_none()
        if not ak:
            return None
        # Update last used
        ak.last_used_at = datetime.now(timezone.utc)
        await session.commit()
        return {"key_id": ak.id, "name": ak.name, "org_id": ak.org_id, "rate_limit": ak.rate_limit}


async def list_api_keys(org_id: str | None = None) -> list[dict]:
    from backend.db.database import async_session
    from backend.db.models_advanced import APIKey
    from sqlalchemy import select

    async with async_session() as session:
        query = select(APIKey)
        if org_id:
            query = query.where(APIKey.org_id == org_id)
        result = await session.execute(query.order_by(APIKey.created_at.desc()))
        return [{"id": ak.id, "name": ak.name, "org_id": ak.org_id, "rate_limit": ak.rate_limit, "is_active": ak.is_active, "created_at": ak.created_at.isoformat()} for ak in result.scalars().all()]


async def revoke_api_key(key_id: str) -> dict:
    from backend.db.database import async_session
    from backend.db.models_advanced import APIKey
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(APIKey).where(APIKey.id == key_id))
        ak = result.scalar_one_or_none()
        if not ak:
            return {"error": "Key not found"}
        ak.is_active = False
        await session.commit()
        return {"status": "revoked"}
