"""Audit Trail — records events on investigation cases."""

from backend.db.database import async_session
from backend.db.models_advanced import AuditEvent


class AuditService:
    async def log(self, case_id: str, event_type: str, details: dict | None = None, actor: str = "system"):
        async with async_session() as session:
            session.add(AuditEvent(case_id=case_id, event_type=event_type, details=details or {}, actor=actor))
            await session.commit()

    async def get_timeline(self, case_id: str) -> list[dict]:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp)
            )
            return [{"event_type": a.event_type, "timestamp": a.timestamp.isoformat(), "details": a.details, "actor": a.actor} for a in result.scalars().all()]
