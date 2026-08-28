"""Tests for all next-gen TruthLens features."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# ============================================================
#  RELIABILITY — Ensemble Engine
# ============================================================

class TestEnsembleEngine:
    def test_high_agreement(self):
        from backend.services.ensemble_engine import ModelSignal, compute_ensemble
        signals = [
            ModelSignal(model_id="a", model_version="1", label="fake", confidence=0.9),
            ModelSignal(model_id="b", model_version="2", label="fake", confidence=0.88),
        ]
        result = compute_ensemble(signals)
        assert result.agreement == "HIGH_AGREEMENT"
        assert result.needs_human_review is False

    def test_strong_disagreement(self):
        from backend.services.ensemble_engine import ModelSignal, compute_ensemble
        signals = [
            ModelSignal(model_id="a", model_version="1", label="fake", confidence=0.9),
            ModelSignal(model_id="b", model_version="2", label="real", confidence=0.8),
        ]
        result = compute_ensemble(signals)
        assert result.agreement == "STRONG_DISAGREEMENT"
        assert result.needs_human_review is True

    def test_single_model(self):
        from backend.services.ensemble_engine import ModelSignal, compute_ensemble
        signals = [ModelSignal(model_id="a", model_version="1", label="fake", confidence=0.9)]
        result = compute_ensemble(signals)
        assert result.agreement == "SINGLE_MODEL"

    def test_api_ensemble(self):
        resp = client.post("/nextgen/ensemble", json={
            "signals": [
                {"model_id": "a", "model_version": "1", "label": "fake", "confidence": 0.9},
                {"model_id": "b", "model_version": "2", "label": "fake", "confidence": 0.85},
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "agreement" in data
        assert "ensemble_confidence" in data


# ============================================================
#  RELIABILITY — Uncertainty Engine
# ============================================================

class TestUncertaintyEngine:
    def test_low_uncertainty(self):
        from backend.services.uncertainty_engine import compute_uncertainty
        result = compute_uncertainty(
            risk_score=80, model_confidence=0.9, evidence_strength=0.8,
            evidence_agreement=0.9, modality_count=3,
            provenance_available=True, fact_check_available=True,
        )
        assert result.level == "LOW"

    def test_high_uncertainty(self):
        from backend.services.uncertainty_engine import compute_uncertainty
        result = compute_uncertainty(
            risk_score=50, model_confidence=0.2, evidence_strength=0.1,
            evidence_agreement=0.2, modality_count=0,
            ensemble_disagreement="HIGH",
        )
        assert result.level in ("HIGH", "CRITICAL")

    def test_api_uncertainty(self):
        resp = client.post("/nextgen/uncertainty", json={
            "risk_score": 50, "model_confidence": 0.5,
            "evidence_strength": 0.5, "modality_count": 2,
        })
        assert resp.status_code == 200
        assert "level" in resp.json()


# ============================================================
#  RELIABILITY — Consistency Checker
# ============================================================

class TestConsistencyChecker:
    def test_consistent_verdict(self):
        from backend.services.consistency_checker import check_verdict_consistency
        result = check_verdict_consistency(risk_score=85, verdict="High Risk", confidence=0.9)
        assert result.is_consistent is True

    def test_inconsistent_verdict(self):
        from backend.services.consistency_checker import check_verdict_consistency
        result = check_verdict_consistency(risk_score=15, verdict="High Risk", confidence=0.9)
        assert result.is_consistent is False
        assert result.suggested_verdict == "Low"

    def test_api_consistency(self):
        resp = client.post("/nextgen/consistency-check", json={
            "risk_score": 80, "verdict": "High Risk", "confidence": 0.85,
        })
        assert resp.status_code == 200
        assert "is_consistent" in resp.json()


# ============================================================
#  RELIABILITY — Evidence Quality
# ============================================================

class TestEvidenceQuality:
    def test_high_quality(self):
        from backend.services.evidence_quality import compute_evidence_quality
        result = compute_evidence_quality(
            num_sources=5, source_reliability=0.9,
            agreement=0.9, completeness=0.8,
            provenance_available=True,
        )
        assert result.score >= 70
        assert result.grade in ("A", "B")

    def test_low_quality(self):
        from backend.services.evidence_quality import compute_evidence_quality
        result = compute_evidence_quality(
            num_sources=0, source_reliability=0.1,
            agreement=0.1, completeness=0.1,
        )
        assert result.score < 30

    def test_api_evidence_quality(self):
        resp = client.post("/nextgen/evidence-quality", json={
            "num_sources": 3, "source_reliability": 0.7,
            "agreement": 0.8, "provenance_available": True,
        })
        assert resp.status_code == 200
        assert "score" in resp.json()
        assert "grade" in resp.json()


# ============================================================
#  RELIABILITY — Counterfactual Explanations
# ============================================================

class TestCounterfactuals:
    def test_counterfactuals_generate_scenarios(self):
        from backend.services.counterfactual_engine import compute_counterfactuals
        result = compute_counterfactuals(current_risk=80)
        assert len(result.scenarios) >= 1
        assert result.current_risk == 80

    def test_api_counterfactuals(self):
        resp = client.post("/nextgen/counterfactuals", json={"current_risk": 75})
        assert resp.status_code == 200
        data = resp.json()
        assert "scenarios" in data
        assert "disclaimer" in data


# ============================================================
#  RELIABILITY — Decision Matrix
# ============================================================

class TestDecisionMatrix:
    def test_high_risk_high_evidence(self):
        from backend.services.decision_matrix import make_decision
        result = make_decision(risk_score=85, evidence_strength=0.8)
        assert result["assessment"] == "HIGH RISK"

    def test_low_risk_high_evidence(self):
        from backend.services.decision_matrix import make_decision
        result = make_decision(risk_score=15, evidence_strength=0.8)
        assert result["assessment"] == "LOW RISK"

    def test_high_risk_low_evidence(self):
        from backend.services.decision_matrix import make_decision
        result = make_decision(risk_score=85, evidence_strength=0.1)
        assert result["assessment"] == "REVIEW REQUIRED"

    def test_api_decision(self):
        resp = client.post("/nextgen/decision", json={
            "risk_score": 80, "evidence_strength": 0.7,
        })
        assert resp.status_code == 200
        assert "assessment" in resp.json()


# ============================================================
#  RELIABILITY — Explanation Quality
# ============================================================

class TestExplanationQuality:
    def test_supported_explanation(self):
        from backend.services.explanation_engine import verify_explanation
        result = verify_explanation(
            "Video shows manipulation",
            has_model_signal=True, has_evidence=True, has_provenance=True,
        )
        assert result["is_supported"] is True

    def test_unsupported_explanation(self):
        from backend.services.explanation_engine import verify_explanation
        result = verify_explanation("This is fake", has_model_signal=False, has_evidence=False)
        assert result["is_supported"] is False
        assert result["warning"] is not None

    def test_api_explanation_quality(self):
        resp = client.post("/nextgen/explanation-quality", json={
            "explanation": "Video shows signs of manipulation",
            "has_model_signal": True,
            "has_evidence": True,
        })
        assert resp.status_code == 200


# ============================================================
#  SECURITY — Sandbox Validation
# ============================================================

class TestSandbox:
    def test_validate_good_image(self):
        import io
        from PIL import Image
        img = Image.new("RGB", (100, 100), "blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        resp = client.post("/nextgen/sandbox/validate",
            files={"file": ("test.jpg", buf, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["file_type"] == "image"

    def test_reject_empty_file(self):
        resp = client.post("/nextgen/sandbox/validate",
            files={"file": ("empty.jpg", b"", "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False

    def test_privacy_info(self):
        resp = client.get("/nextgen/privacy/info")
        assert resp.status_code == 200
        assert "stored" in resp.json()
        assert "temporary" in resp.json()

    def test_retention_policies(self):
        resp = client.get("/nextgen/retention/policies")
        assert resp.status_code == 200
        policies = resp.json()
        assert "media" in policies
        assert "audit" in policies


# ============================================================
#  SECURITY — Security Events
# ============================================================

class TestSecurityEvents:
    def test_record_and_retrieve(self):
        from backend.services.security_events import record_event, get_recent_events
        record_event("TEST_EVENT", "INFO", {"test": True})
        events = get_recent_events(limit=5)
        assert len(events) >= 1
        assert events[0]["event_type"] == "TEST_EVENT"

    def test_api_security_events(self):
        resp = client.get("/nextgen/security/events")
        assert resp.status_code == 200

    def test_api_security_stats(self):
        resp = client.get("/nextgen/security/stats")
        assert resp.status_code == 200
        assert "total_events" in resp.json()


# ============================================================
#  PERFORMANCE — Jobs
# ============================================================

class TestJobs:
    def test_create_and_get_job(self):
        resp = client.post("/nextgen/jobs", json={"priority": "HIGH"})
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        resp = client.get(f"/nextgen/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "QUEUED"

    def test_list_jobs(self):
        resp = client.get("/nextgen/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_cancel_job(self):
        resp = client.post("/nextgen/jobs", json={"priority": "NORMAL"})
        job_id = resp.json()["job_id"]
        resp = client.post(f"/nextgen/jobs/{job_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"


# ============================================================
#  PERFORMANCE — Cache
# ============================================================

class TestCache:
    def test_cache_miss(self):
        resp = client.post("/nextgen/cache/check", json={"sha256": "nonexistent"})
        assert resp.status_code == 200
        assert resp.json()["hit"] is False

    def test_cache_stats(self):
        resp = client.get("/nextgen/cache/stats")
        assert resp.status_code == 200
        assert "size" in resp.json()

    def test_clear_cache(self):
        resp = client.post("/nextgen/cache/clear")
        assert resp.status_code == 200


# ============================================================
#  RESEARCH — Drift Detection
# ============================================================

class TestDriftDetection:
    def test_record_and_detect(self):
        from backend.services.drift_service import record_observation, detect_drift
        for _ in range(20):
            record_observation(confidence=0.7, label="fake", modality="text")
        result = detect_drift()
        assert "status" in result
        assert result["observations_count"] >= 20

    def test_api_drift(self):
        resp = client.get("/nextgen/drift/detect")
        assert resp.status_code == 200


# ============================================================
#  OPERATIONS — System Health
# ============================================================

class TestSystemHealth:
    def test_health_endpoint(self):
        resp = client.get("/nextgen/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert "components" in data
        assert "metrics" in data


# ============================================================
#  OPERATIONS — Traces
# ============================================================

class TestTraces:
    def test_create_and_list_traces(self):
        from backend.services.trace_service import start_trace, complete_trace, list_traces
        t = start_trace(input_types=["text"])
        complete_trace(t["trace_id"])
        traces = list_traces()
        assert len(traces) >= 1

    def test_api_traces(self):
        resp = client.get("/nextgen/traces")
        assert resp.status_code == 200

    def test_trace_summary(self):
        resp = client.get("/nextgen/traces/summary")
        assert resp.status_code == 200
        assert "total_traces" in resp.json()


# ============================================================
#  DEVELOPER — Snapshots
# ============================================================

class TestSnapshots:
    def test_create_and_get_snapshots(self):
        from backend.services.snapshot_service import create_snapshot, get_snapshots
        s = create_snapshot(case_id="TEST-CASE", risk_score=75, verdict="High Risk")
        assert s["version"] == 1
        snaps = get_snapshots("TEST-CASE")
        assert len(snaps) == 1

    def test_multiple_snapshots(self):
        from backend.services.snapshot_service import create_snapshot, get_snapshots
        create_snapshot(case_id="TEST-CASE-2", risk_score=70)
        create_snapshot(case_id="TEST-CASE-2", risk_score=65, verdict="Review Needed")
        snaps = get_snapshots("TEST-CASE-2")
        assert len(snaps) == 2
        assert snaps[1]["version"] == 2


# ============================================================
#  API — Full Next-Gen Analysis
# ============================================================

class TestFullNextGenAnalysis:
    def test_text_full_analysis(self):
        resp = client.post("/nextgen/full-analysis",
            data={"text": "Breaking: aliens land in Times Square", "modality": "text"})
        assert resp.status_code == 200
        data = resp.json()
        assert "trace_id" in data
        assert "prediction" in data
        assert "ensemble" in data
        assert "uncertainty" in data
        assert "consistency" in data
        assert "evidence_quality" in data
        assert "counterfactuals" in data
        assert "decision" in data
