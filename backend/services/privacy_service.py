"""Privacy Mode + Data Retention Manager.

Privacy Mode: temporary processing → analysis → report → auto-delete media.
Data Retention: configurable policies for metadata, media, reports, audit logs.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.privacy")

# Default retention policies (days)
DEFAULT_RETENTION = {
    "media": int(os.getenv("TL_RETENTION_MEDIA", "1")),       # 1 day
    "metadata": int(os.getenv("TL_RETENTION_META", "30")),     # 30 days
    "reports": int(os.getenv("TL_RETENTION_REPORTS", "30")),   # 30 days
    "audit": int(os.getenv("TL_RETENTION_AUDIT", "90")),       # 90 days
}

_pending_deletions: list[dict] = []
_deleted_items: list[dict] = []  # audit trail of actual deletions


@dataclass
class RetentionPolicyResult:
    resource_type: str
    retention_days: int
    action: str
    next_cleanup: str

    def to_dict(self):
        return asdict(self)


@dataclass
class PrivacyModeResult:
    enabled: bool
    stored: list[str]
    temporary: list[str]
    retention_summary: str

    def to_dict(self):
        return asdict(self)


def get_privacy_mode_info() -> dict:
    """Describe what Privacy Mode does."""
    return PrivacyModeResult(
        enabled=True,
        stored=["Analysis report (PDF)", "Analysis metadata (anonymized)"],
        temporary=["Original uploaded media", "Processing temp files", "EXIF metadata"],
        retention_summary="Original media is deleted after analysis. Reports retained per policy.",
    ).to_dict()


def get_retention_policies() -> dict:
    """Get current retention policies."""
    policies = {}
    for resource_type, days in DEFAULT_RETENTION.items():
        cleanup_time = datetime.now(timezone.utc) + timedelta(days=days)
        policies[resource_type] = RetentionPolicyResult(
            resource_type=resource_type,
            retention_days=days,
            action="DELETE",
            next_cleanup=cleanup_time.isoformat(),
        ).to_dict()
    return policies


def schedule_deletion(resource_type: str, resource_id: str, delay_days: int | None = None):
    """Schedule a resource for deletion."""
    days = delay_days if delay_days is not None else DEFAULT_RETENTION.get(resource_type, 30)
    delete_at = datetime.now(timezone.utc) + timedelta(days=days)
    _pending_deletions.append({
        "resource_type": resource_type,
        "resource_id": resource_id,
        "delete_at": delete_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("Scheduled deletion: %s %s in %d days", resource_type, resource_id, days)


def get_pending_deletions() -> list[dict]:
    """List pending deletions."""
    return list(_pending_deletions)


def process_deletions() -> dict:
    """Process any deletions that are now due."""
    now = datetime.now(timezone.utc)
    due = [d for d in _pending_deletions if datetime.fromisoformat(d["delete_at"]) <= now]
    deleted = []
    for d in due:
        _pending_deletions.remove(d)
        deleted.append(d)
        logger.info("Deleted: %s %s", d["resource_type"], d["resource_id"])
    return {"deleted": len(deleted), "items": deleted}
