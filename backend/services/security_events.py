"""Security Event Log.

Separate security-oriented event stream, distinct from the audit trail.
Tracks invalid uploads, rate limits, auth failures, suspicious patterns.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

logger = logging.getLogger("truthlens.security")

# In-memory ring buffer for recent events (persisted to DB when available)
_events: list[dict] = []
_MAX_BUFFER = 500


@dataclass
class SecurityEvent:
    event_type: str  # INVALID_UPLOAD, RATE_LIMIT, AUTH_FAILURE, etc
    severity: str  # INFO, WARN, CRITICAL
    details: dict
    source_ip: str | None = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return asdict(self)


def record_event(
    event_type: str,
    severity: str = "INFO",
    details: dict | None = None,
    source_ip: str | None = None,
) -> dict:
    """Record a security event."""
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        details=details or {},
        source_ip=source_ip,
    )
    d = event.to_dict()
    _events.append(d)
    # Ring buffer
    if len(_events) > _MAX_BUFFER:
        _events.pop(0)

    log_fn = logger.warning if severity in ("WARN", "CRITICAL") else logger.info
    log_fn("SECURITY [%s] %s: %s", severity, event_type, details)

    # Try to persist to DB
    try:
        import asyncio
        from backend.db.database import async_session
        from backend.db.models_reliability import SecurityEvent as DBEvent

        async def _persist():
            async with async_session() as session:
                session.add(DBEvent(
                    event_type=event_type,
                    severity=severity,
                    details=details or {},
                    source_ip=source_ip,
                ))
                await session.commit()

        # Fire and forget — don't block the request
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist())
        except RuntimeError:
            pass  # No event loop — skip persistence
    except Exception:
        pass  # DB not available — memory buffer is fine

    return d


def get_recent_events(limit: int = 50, severity: str | None = None) -> list[dict]:
    """Get recent security events from the buffer."""
    events = _events
    if severity:
        events = [e for e in events if e["severity"] == severity]
    return list(reversed(events[-limit:]))


def get_event_stats() -> dict:
    """Get summary stats of security events."""
    total = len(_events)
    by_type = {}
    by_severity = {"INFO": 0, "WARN": 0, "CRITICAL": 0}
    for e in _events:
        by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
        by_severity[e["severity"]] = by_severity.get(e["severity"], 0) + 1
    return {
        "total_events": total,
        "by_type": by_type,
        "by_severity": by_severity,
    }
