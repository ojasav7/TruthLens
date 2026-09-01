"""Review Workflow — assign reviewers, add comments, override verdicts, audit trail. SQLite-backed."""

import uuid
from datetime import datetime, timezone
from backend.services.db_persist import save_workflow, load_workflow, load_all_workflows


def _now():
    return datetime.now(timezone.utc).isoformat()


def _event(reviewer_id: str, action: str, details: dict) -> dict:
    return {"event_id": str(uuid.uuid4()), "timestamp": _now(), "reviewer_id": reviewer_id, "action": action, **details}


def _get(analysis_id: str) -> dict:
    w = load_workflow(analysis_id)
    if w is None:
        w = {
            "analysis_id": analysis_id,
            "status": "pending",
            "assigned_reviewer": None,
            "comments": [],
            "verdict_overrides": [],
            "final_disposition": None,
            "audit_trail": [_event("system", "workflow_created", {"status": "pending"})],
            "created_at": _now(),
        }
    return w


def _save(w: dict):
    save_workflow(w["analysis_id"], w)


def assign_reviewer(analysis_id: str, reviewer_id: str) -> dict:
    w = _get(analysis_id)
    w["assigned_reviewer"] = reviewer_id
    w["status"] = "in_review"
    w["audit_trail"].append(_event(reviewer_id, "reviewer_assigned", {"reviewer_id": reviewer_id}))
    _save(w)
    return w


def add_comment(analysis_id: str, reviewer_id: str, comment: str) -> dict:
    w = _get(analysis_id)
    entry = {"id": str(uuid.uuid4()), "reviewer_id": reviewer_id, "comment": comment, "timestamp": _now()}
    w["comments"].append(entry)
    w["audit_trail"].append(_event(reviewer_id, "comment_added", {"comment_id": entry["id"]}))
    _save(w)
    return w


def override_verdict(analysis_id: str, reviewer_id: str, new_verdict: str, reason: str) -> dict:
    w = _get(analysis_id)
    prev = w["verdict_overrides"][-1]["new_verdict"] if w["verdict_overrides"] else None
    w["verdict_overrides"].append({"new_verdict": new_verdict, "reason": reason, "reviewer_id": reviewer_id, "timestamp": _now()})
    w["audit_trail"].append(_event(reviewer_id, "verdict_overridden", {"previous": prev, "new": new_verdict, "reason": reason}))
    _save(w)
    return w


def set_disposition(analysis_id: str, reviewer_id: str, disposition: str) -> dict:
    w = _get(analysis_id)
    w["final_disposition"] = disposition
    w["status"] = "reviewed"
    w["audit_trail"].append(_event(reviewer_id, "disposition_set", {"disposition": disposition}))
    _save(w)
    return w


def get_audit_trail(analysis_id: str) -> list:
    return _get(analysis_id)["audit_trail"]


def list_workflows() -> list:
    return load_all_workflows()
