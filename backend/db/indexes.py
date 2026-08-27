"""Database indexes — created after tables via lifespan startup."""

from sqlalchemy import text


INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_verdict ON analyses(verdict)",
    "CREATE INDEX IF NOT EXISTS idx_analyses_threat ON analyses(threat_score)",
    "CREATE INDEX IF NOT EXISTS idx_cases_status ON investigation_cases(status)",
    "CREATE INDEX IF NOT EXISTS idx_cases_priority ON investigation_cases(priority)",
    "CREATE INDEX IF NOT EXISTS idx_cases_created ON investigation_cases(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_events(case_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_fingerprint_sha ON media_fingerprints(sha256)",
    "CREATE INDEX IF NOT EXISTS idx_fingerprint_media ON media_fingerprints(media_id)",
    "CREATE INDEX IF NOT EXISTS idx_apikey_hash ON api_keys(key_hash)",
]


async def create_indexes():
    """Call from lifespan after create_all."""
    from backend.db.database import engine
    async with engine.begin() as conn:
        for stmt in INDEXES:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # table may not exist yet
