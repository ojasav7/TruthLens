"""Timeline Investigation — tracks publication, edits, shares, analysis events."""

import uuid
from datetime import datetime, timezone

_investigations = {}  # content_id -> dict


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get(content_id: str) -> dict:
    if content_id not in _investigations:
        _investigations[content_id] = {
            "content_id": content_id,
            "events": [],
            "created_at": _now(),
        }
    return _investigations[content_id]


def add_event(content_id: str, event_type: str, source: str, details: dict = None) -> dict:
    inv = _get(content_id)
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": _now(),
        "event_type": event_type,
        "source": source,
        "details": details or {},
    }
    inv["events"].append(event)
    return event


def get_timeline(content_id: str) -> dict:
    inv = _get(content_id)
    return {"content_id": content_id, "events": inv["events"], "total_events": len(inv["events"])}


def generate_summary(content_id: str) -> str:
    events = _get(content_id)["events"]
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
