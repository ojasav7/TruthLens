"""Advanced features — fingerprint, graph, benchmark, calibration, radar, robustness, human-explain."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# --- Media Fingerprint ---
@router.post("/fingerprint")
async def create_fingerprint(file: UploadFile = File(...)):
    """Create a unique media fingerprint (SHA-256 + TL-M ID)."""
    from backend.services.fingerprint_service import create_fingerprint as _create
    data = await file.read()
    return await _create(data, file.filename or "unknown", file.content_type or "application/octet-stream")


@router.get("/fingerprint/lookup/{sha256}")
async def lookup_fingerprint(sha256: str):
    """Look up existing media by SHA-256 hash."""
    from backend.services.fingerprint_service import lookup_by_hash
    result = await lookup_by_hash(sha256)
    if not result:
        raise HTTPException(status_code=404, detail="Fingerprint not found")
    return result


# --- Evidence Graph ---
@router.get("/graph/{case_id}")
async def get_evidence_graph(case_id: str):
    """Get evidence graph (nodes + edges) for an investigation."""
    from backend.services.graph_service import build_graph
    result = await build_graph(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# --- Robustness Lab ---
@router.post("/robustness")
async def run_robustness(file: UploadFile = File(...)):
    """Run robustness test — apply transformations and measure prediction stability."""
    from backend.services.robustness_service import run_robustness_test
    data = await file.read()
    return await run_robustness_test(data, file.filename or "test", file.content_type or "image/png")


# --- Model Benchmark ---
@router.get("/benchmarks")
async def get_benchmarks(modality: str | None = Query(None)):
    """Get model benchmark results."""
    from backend.services.benchmark_service import get_benchmarks as _get
    return _get(modality)


@router.get("/models/versions")
async def get_model_versions():
    """Get all model versions and their benchmark data."""
    from backend.services.benchmark_service import get_versions
    return get_versions()


# --- Confidence Calibration ---
@router.get("/calibration")
async def get_calibration():
    """Get confidence calibration analysis — predicted vs actual accuracy."""
    from backend.db.database import async_session
    from backend.db.models import Analysis
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Analysis.breakdown))
        breakdowns = [row[0] for row in result.all() if row[0]]

    if not breakdowns:
        return {"buckets": {}, "message": "No data for calibration analysis"}

    # Group confidences into buckets
    buckets = {}
    for bd in breakdowns:
        for mod in ["text", "image", "video", "audio"]:
            if mod in bd and isinstance(bd[mod], dict) and "confidence" in bd[mod]:
                conf = bd[mod]["confidence"]
                label = bd[mod].get("label", "unknown")
                bucket = f"{int(conf * 10) * 10}-{int(conf * 10) * 10 + 10}%"
                buckets.setdefault(bucket, {"count": 0, "fake_count": 0, "real_count": 0})
                buckets[bucket]["count"] += 1
                if label in ("fake", "cloned"):
                    buckets[bucket]["fake_count"] += 1
                else:
                    buckets[bucket]["real_count"] += 1

    # Add "actual accuracy" (fake detection rate) per bucket
    calibration = {}
    for bucket, data in sorted(buckets.items()):
        total = data["count"]
        fake_rate = round(data["fake_count"] / total, 2) if total else 0
        calibration[bucket] = {"count": total, "fake_detection_rate": fake_rate, "midpoint": int(bucket.split("-")[0]) + 5}

    return {"buckets": calibration, "total_samples": sum(d["count"] for d in buckets.values())}


# --- Misinformation Radar ---
@router.get("/radar")
async def get_radar():
    """Aggregate analytics across all analyses."""
    from backend.services.analytics_service import get_radar as _radar
    return await _radar()


# --- Explain Like I'm Human ---
@router.get("/explain-human/{case_id}")
async def explain_human(case_id: str):
    """Get plain-English explanation for an investigation."""
    from backend.services.investigation_service import InvestigationService
    from backend.services.human_explainer import explain_investigation

    inv = InvestigationService()
    result = await inv.get_investigation(case_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return explain_investigation(result)
