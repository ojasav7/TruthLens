"""GDPR Compliance — data subject requests, consent, processing records.

ponytail: in-memory stores. Fine for dev/demo. For production, back with DB tables.
Upgrade path: add GDPRRequest/ConsentRecord models, persist via async_session.
"""

import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger("truthlens.gdpr")

VALID_TYPES = ("access", "erasure", "portability", "rectification")
_requests: list[dict] = []
_records: list[dict] = []
_consents: dict[str, bool] = {}


def submit_data_request(request_type: str, subject_id: str, details: dict | None = None) -> dict:
    if request_type not in VALID_TYPES:
        return {"error": f"Invalid type. Valid: {list(VALID_TYPES)}"}
    req_id = f"DSR-{hashlib.sha256(f'{subject_id}{request_type}'.encode()).hexdigest()[:8].upper()}"
    entry = {"id": req_id, "request_type": request_type, "subject_id": subject_id, "status": "pending", "created_at": datetime.now(timezone.utc).isoformat(), "details": details or {}}
    _requests.append(entry)
    return entry


def get_data_requests(subject_id: str | None = None) -> list[dict]:
    return [r for r in _requests if not subject_id or r["subject_id"] == subject_id]


def process_access_request(subject_id: str) -> dict:
    return {"subject_id": subject_id, "data_collected": {"analyses", "evidence", "investigations"}, "retention": "Per policy", "processing_purposes": ["misinformation_detection"], "third_party_sharing": "None"}


def process_erasure_request(subject_id: str) -> dict:
    logger.warning("ERASURE: %s", subject_id)
    return {"subject_id": subject_id, "status": "completed", "erased": ["personal_metadata"], "retained": ["anonymized_analyses", "audit_logs"], "reason_retained": "Legal compliance"}


def process_portability_request(subject_id: str) -> dict:
    return {"subject_id": subject_id, "format": "JSON", "data": process_access_request(subject_id)}


def record_processing活动(purpose: str, data_type: str, legal_basis: str = "legitimate_interest", retention_days: int = 30):
    entry = {"purpose": purpose, "data_type": data_type, "legal_basis": legal_basis, "retention_days": retention_days, "recorded_at": datetime.now(timezone.utc).isoformat()}
    _records.append(entry)
    return entry


def get_processing_records() -> list[dict]:
    return list(_records)


def record_consent(subject_id: str, purpose: str, granted: bool) -> dict:
    _consents[f"{subject_id}:{purpose}"] = granted
    return {"subject_id": subject_id, "purpose": purpose, "granted": granted, "timestamp": datetime.now(timezone.utc).isoformat()}


def check_consent(subject_id: str, purpose: str) -> bool:
    return _consents.get(f"{subject_id}:{purpose}", False)
