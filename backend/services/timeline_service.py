"""Timeline Investigation — tracks publication, edits, shares, analysis events. SQLite-backed."""

import uuid
from datetime import datetime, timezone
from backend.services.db_persist import save_timeline_event, load_timeline


def _now():
    return datetime.now(timezone.utc).isoformat()


def add_event(content_id: str, event_type: str, source: str, details: dict = None) -> dict:
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": _now(),
        "event_type": event_type,
        "source": source,
        "details": details or {},
    }
    save_timeline_event(content_id, event_type, source, details)
    return event


def get_timeline(content_id: str) -> dict:
    events = load_timeline(content_id)
    return {"content_id": content_id, "events": events, "total_events": len(events)}


def generate_summary(content_id: str) -> str:
    events = load_timeline(content_id)
    if not events:
        return "No events recorded."
    by_type = {}
    for e in events:
        t = e["event_type"]
        by_type[t] = by_type.get(t, 0) + 1
    parts = [f"{len(events)} events recorded."]
    for t, count in by_type.items():
        parts.append(f"{t}: {count}x.")
    return " ".join(parts)
