"""Investigation Snapshots.

Every major investigation state is reproducible. Snapshots contain
analysis ID, model versions, evidence IDs, risk, verdict, uncertainty, config.
"""

import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger("truthlens.snapshot")

_snapshots: dict[str, list[dict]] = {}  # case_id → [snapshots]


@dataclass
class SnapshotData:
    case_id: str
    version: int
    analysis_id: str | None = None
    risk_score: float | None = None
    verdict: str | None = None
    uncertainty: str | None = None
    evidence_ids: list[str] = None
    model_versions: dict = None
    feature_config: dict = None

    def to_dict(self):
        d = asdict(self)
        if d["evidence_ids"] is None:
            d["evidence_ids"] = []
        if d["model_versions"] is None:
            d["model_versions"] = {}
        if d["feature_config"] is None:
            d["feature_config"] = {}
        return d


def create_snapshot(
    case_id: str,
    analysis_id: str | None = None,
    risk_score: float | None = None,
    verdict: str | None = None,
    uncertainty: str | None = None,
    evidence_ids: list[str] | None = None,
    model_versions: dict | None = None,
    feature_config: dict | None = None,
) -> dict:
    """Create a new snapshot for a case."""
    existing = _snapshots.get(case_id, [])
    version = len(existing) + 1

    snap = SnapshotData(
        case_id=case_id,
        version=version,
        analysis_id=analysis_id,
        risk_score=risk_score,
        verdict=verdict,
        uncertainty=uncertainty,
        evidence_ids=evidence_ids or [],
        model_versions=model_versions or {},
        feature_config=feature_config or {},
    )

    d = snap.to_dict()
    _snapshots.setdefault(case_id, []).append(d)
    logger.info("Snapshot v%d created for case %s", version, case_id)
    return d


def get_snapshots(case_id: str) -> list[dict]:
    return _snapshots.get(case_id, [])


def get_snapshot(case_id: str, version: int) -> dict | None:
    snaps = _snapshots.get(case_id, [])
    if 0 < version <= len(snaps):
        return snaps[version - 1]
    return None
