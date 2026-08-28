"""Investigation Export Package.

Creates a complete investigation package with all data, hashes, and metadata.
Privacy: does not include original media without explicit authorization.
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.export")


def build_export_package(
    investigation: dict,
    evidence: list[dict] | None = None,
    analyses: list[dict] | None = None,
    timeline: list[dict] | None = None,
    model_versions: list[dict] | None = None,
    audit_log: list[dict] | None = None,
    snapshots: list[dict] | None = None,
    conflicts: dict | None = None,
    integrity: dict | None = None,
    include_media: bool = False,
) -> dict:
    """Build a complete investigation export package."""
    package = {
        "package_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "truthlens_version": "1.0.0",
        "investigation": investigation,
        "evidence": evidence or [],
        "analyses": analyses or [],
        "timeline": timeline or [],
        "model_versions": model_versions or [],
        "audit_log": audit_log or [],
        "snapshots": snapshots or [],
        "conflicts": conflicts or {},
        "integrity": integrity or {},
        "limitations": _generate_limitations(evidence, analyses),
        "privacy": {
            "original_media_included": include_media,
            "notice": "Original media excluded by default. Set include_media=true to include." if not include_media else "Original media included — handle in accordance with applicable policies.",
        },
    }

    # Compute package hash for integrity verification
    package_bytes = json.dumps(package, sort_keys=True, default=str).encode()
    package["package_hash"] = hashlib.sha256(package_bytes).hexdigest()

    return package


def _generate_limitations(evidence: list[dict] | None, analyses: list[dict] | None) -> list[str]:
    """Generate limitations from actual system state."""
    limitations = []
    if not evidence:
        limitations.append("No evidence records available")
    elif len(evidence) < 3:
        limitations.append("Limited evidence diversity")

    if not analyses:
        limitations.append("No analysis results available")

    has_provenance = any(
        e.get("type") == "provenance" for e in (evidence or [])
    )
    if not has_provenance:
        limitations.append("Provenance data not available")

    has_source = any(
        e.get("type") == "source" for e in (evidence or [])
    )
    if not has_source:
        limitations.append("Independent source verification not available")

    return limitations


def get_export_manifest(package: dict) -> dict:
    """Get a summary manifest of the export package."""
    return {
        "package_hash": package.get("package_hash"),
        "exported_at": package.get("exported_at"),
        "sections": {
            "investigation": bool(package.get("investigation")),
            "evidence_count": len(package.get("evidence", [])),
            "analysis_count": len(package.get("analyses", [])),
            "timeline_events": len(package.get("timeline", [])),
            "audit_events": len(package.get("audit_log", [])),
            "snapshots": len(package.get("snapshots", [])),
            "limitations": len(package.get("limitations", [])),
        },
    }
