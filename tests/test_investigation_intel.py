"""Tests for Investigation Intelligence features."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# ============================================================
#  CHAIN OF CUSTODY
# ============================================================

class TestChainOfCustody:
    def test_record_and_get_chain(self):
        from backend.services.chain_of_custody import record_event, get_chain
        record_event("E-TEST-001", "evidence_created", actor="system")
        record_event("E-TEST-001", "evidence_analyzed", actor="model", new_state="analyzed")
        chain = get_chain("E-TEST-001")
        assert len(chain) == 2
        assert chain[0]["event_type"] == "evidence_created"
        assert chain[1]["event_type"] == "evidence_analyzed"
        # Verify immutability — original events unchanged
        assert chain[0]["new_state"] is None

    def test_api_custody(self):
        resp = client.post("/investigation-intel/custody/events", json={
            "evidence_id": "E-API-001", "event_type": "evidence_uploaded",
        })
        assert resp.status_code == 200
        resp = client.get("/investigation-intel/custody/E-API-001")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ============================================================
#  INVESTIGATION TIMELINE
# ============================================================

class TestTimeline:
    def test_add_and_get_timeline(self):
        from backend.services.timeline_service import add_event, get_timeline
        add_event("CASE-001", "upload", description="Media uploaded")
        add_event("CASE-001", "analysis", description="Image analyzed", module="image")
        timeline = get_timeline("CASE-001")
        assert len(timeline) == 2
        assert timeline[0]["event_type"] == "upload"

    def test_filter_by_event_type(self):
        from backend.services.timeline_service import add_event, get_timeline
        add_event("CASE-002", "upload")
        add_event("CASE-002", "analysis")
        add_event("CASE-002", "upload")
        uploads = get_timeline("CASE-002", event_type="upload")
        assert len(uploads) == 2

    def test_api_timeline(self):
        client.post("/investigation-intel/timeline/events", json={
            "case_id": "CASE-API", "event_type": "upload", "description": "test",
        })
        resp = client.get("/investigation-intel/investigations/CASE-API/timeline")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ============================================================
#  INVESTIGATION CONFIDENCE
# ============================================================

class TestInvestigationConfidence:
    def test_high_confidence(self):
        from backend.services.investigation_confidence import compute_investigation_confidence
        result = compute_investigation_confidence(
            model_agreement=0.9, evidence_quality=0.85, source_diversity=0.8,
            provenance_available=True, claim_verification=0.8,
            cross_modal_agreement=0.9, contradiction_level=0.05,
        )
        assert result["score"] >= 75
        assert result["level"] == "HIGH"

    def test_low_confidence(self):
        from backend.services.investigation_confidence import compute_investigation_confidence
        result = compute_investigation_confidence(
            model_agreement=0.2, evidence_quality=0.1, source_diversity=0.1,
            provenance_available=False, contradiction_level=0.8,
        )
        assert result["score"] < 40

    def test_api_confidence(self):
        resp = client.post("/investigation-intel/investigation-confidence", json={
            "model_agreement": 0.8, "evidence_quality": 0.7,
        })
        assert resp.status_code == 200
        assert "score" in resp.json()
        assert "factors" in resp.json()


# ============================================================
#  INVESTIGATION INTEGRITY SCORE
# ============================================================

class TestIntegrityScore:
    def test_high_integrity(self):
        from backend.services.integrity_score import compute_integrity_score
        result = compute_integrity_score(
            evidence_completeness=0.9, source_diversity=0.85,
            model_agreement=0.9, provenance=0.8,
            evidence_consistency=0.9, reproducibility=0.95,
        )
        assert result["score"] >= 80

    def test_api_integrity(self):
        resp = client.post("/investigation-intel/integrity-score", json={
            "evidence_completeness": 0.8, "provenance": 0.7,
        })
        assert resp.status_code == 200
        assert "score" in resp.json()
        assert "components" in resp.json()


# ============================================================
#  EVIDENCE CONFLICT RESOLVER
# ============================================================

class TestConflictResolver:
    def test_no_conflicts(self):
        from backend.services.conflict_resolver import detect_and_resolve_conflicts
        items = [
            {"id": "E1", "label": "fake", "confidence": 0.8, "source": "model"},
            {"id": "E2", "label": "fake", "confidence": 0.7, "source": "model2"},
        ]
        result = detect_and_resolve_conflicts(items)
        assert result["total_conflicts"] == 0

    def test_detects_conflicts(self):
        from backend.services.conflict_resolver import detect_and_resolve_conflicts
        items = [
            {"id": "E1", "label": "fake", "confidence": 0.9, "source": "model"},
            {"id": "E2", "label": "real", "confidence": 0.85, "source": "source_a"},
        ]
        result = detect_and_resolve_conflicts(items)
        assert result["total_conflicts"] >= 1
        assert result["overall_severity"] in ("LOW", "MEDIUM", "HIGH")

    def test_api_conflicts(self):
        resp = client.post("/investigation-intel/conflicts", json={
            "evidence_items": [
                {"id": "E1", "label": "fake", "confidence": 0.9, "source": "m1"},
                {"id": "E2", "label": "real", "confidence": 0.85, "source": "m2"},
            ]
        })
        assert resp.status_code == 200
        assert "conflicts" in resp.json()


# ============================================================
#  EVIDENCE DEPENDENCY GRAPH
# ============================================================

class TestDependencyGraph:
    def test_build_graph(self):
        from backend.services.dependency_graph import build_dependency_graph
        evidence = [
            {"id": "E1", "type": "model_signal", "category": "POSITIVE"},
            {"id": "E2", "type": "source", "category": "NEGATIVE"},
        ]
        conclusion = {"verdict": "High Risk", "risk_score": 80}
        graph = build_dependency_graph(evidence_items=evidence, conclusion=conclusion)
        assert len(graph["nodes"]) >= 3  # 2 evidence + 1 conclusion
        assert len(graph["edges"]) >= 2

    def test_query_dependency(self):
        from backend.services.dependency_graph import build_dependency_graph, query_dependency
        evidence = [{"id": "E1", "category": "POSITIVE"}, {"id": "E2", "category": "NEGATIVE"}]
        conclusion = {"verdict": "High Risk", "risk_score": 80}
        graph = build_dependency_graph(evidence_items=evidence, conclusion=conclusion)
        result = query_dependency(graph, "E1")
        assert "supports" in result
        assert "contradicts" in result

    def test_api_dependency(self):
        resp = client.post("/investigation-intel/dependency-graph", json={
            "evidence_items": [{"id": "E1", "category": "POSITIVE"}],
            "conclusion": {"verdict": "Low", "risk_score": 15},
        })
        assert resp.status_code == 200
        assert "nodes" in resp.json()
        assert "edges" in resp.json()


# ============================================================
#  WHY NOT CERTAIN?
# ============================================================

class TestWhyNotCertain:
    def test_many_reasons(self):
        from backend.services.why_not_certain import generate_uncertainty_reasons
        result = generate_uncertainty_reasons(
            source_available=False, provenance_available=False,
            model_agreement=False, fact_check_complete=False,
            evidence_count=0, contradiction_count=2,
            original_source_available=False,
        )
        assert result["has_uncertainty"] is True
        assert len(result["reasons"]) >= 4

    def test_no_reasons(self):
        from backend.services.why_not_certain import generate_uncertainty_reasons
        result = generate_uncertainty_reasons(
            source_available=True, provenance_available=True,
            model_agreement=True, fact_check_complete=True,
            audio_quality_sufficient=True, evidence_count=5,
            original_source_available=True,
        )
        assert result["has_uncertainty"] is False

    def test_api_why_not_certain(self):
        resp = client.post("/investigation-intel/why-not-certain", json={
            "provenance_available": False, "evidence_count": 1,
        })
        assert resp.status_code == 200
        assert "reasons" in resp.json()


# ============================================================
#  WHAT WOULD CHANGE MY MIND?
# ============================================================

class TestWhatWouldChange:
    def test_identifies_missing(self):
        from backend.services.what_would_change import identify_missing_evidence
        result = identify_missing_evidence(
            has_original_source=False, has_provenance=False,
            has_independent_source=False, current_risk=80,
        )
        assert result["total_missing"] >= 3
        # Should be prioritized
        priorities = [m["priority"] for m in result["missing_evidence"]]
        assert priorities == sorted(priorities)

    def test_api_what_would_change(self):
        resp = client.post("/investigation-intel/what-would-change", json={
            "current_risk": 75,
        })
        assert resp.status_code == 200
        assert "missing_evidence" in resp.json()


# ============================================================
#  REPRODUCIBILITY
# ============================================================

class TestReproducibility:
    def test_reproducible(self):
        from backend.services.reproducibility import check_reproducibility
        result = check_reproducibility(
            original_signals={"risk_score": 78, "text": {"confidence": 0.9}},
            reproduced_signals={"risk_score": 78, "text": {"confidence": 0.9}},
        )
        assert result["status"] == "REPRODUCIBLE"

    def test_result_difference(self):
        from backend.services.reproducibility import check_reproducibility
        result = check_reproducibility(
            original_signals={"risk_score": 78},
            reproduced_signals={"risk_score": 55},
        )
        assert result["status"] == "RESULT_DIFFERENCE"
        assert result["risk_difference"] > 2.0

    def test_module_difference(self):
        from backend.services.reproducibility import check_reproducibility
        result = check_reproducibility(
            original_signals={"risk_score": 78, "image": {"confidence": 0.81}},
            reproduced_signals={"risk_score": 77, "image": {"confidence": 0.60}},
        )
        assert result["status"] == "MODULE_DIFFERENCE"
        assert len(result["signal_changes"]) >= 1

    def test_analysis_diff(self):
        from backend.services.reproducibility import compute_analysis_diff
        result = compute_analysis_diff(
            original={"threat_score": 78, "verdict": "High Risk", "breakdown": {"image": {"confidence": 0.9}}},
            current={"threat_score": 55, "verdict": "Review Needed", "breakdown": {"image": {"confidence": 0.6}}},
        )
        assert result["total_changes"] >= 2

    def test_api_reproduce(self):
        resp = client.post("/investigation-intel/reproduce", json={
            "original_signals": {"risk_score": 78},
            "reproduced_signals": {"risk_score": 78},
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "REPRODUCIBLE"

    def test_api_diff(self):
        resp = client.post("/investigation-intel/diff", json={
            "original": {"threat_score": 78, "verdict": "High"},
            "current": {"threat_score": 55, "verdict": "Low"},
        })
        assert resp.status_code == 200
        assert resp.json()["total_changes"] >= 1


# ============================================================
#  EXPORT PACKAGE
# ============================================================

class TestExportPackage:
    def test_build_package(self):
        from backend.services.export_package import build_export_package
        pkg = build_export_package(
            investigation={"id": "INV-001", "title": "Test"},
            evidence=[{"id": "E1"}],
        )
        assert "package_hash" in pkg
        assert pkg["privacy"]["original_media_included"] is False
        assert len(pkg["limitations"]) >= 0

    def test_api_export(self):
        resp = client.post("/investigation-intel/export", json={
            "investigation": {"id": "INV-001"},
        })
        assert resp.status_code == 200
        assert "package_hash" in resp.json()


# ============================================================
#  ANNOTATIONS
# ============================================================

class TestAnnotations:
    def test_add_and_get(self):
        from backend.services.annotation_service import add_annotation, get_annotations
        ann = add_annotation("E-ANN-001", "note", "Visual boundary inconsistent", author="analyst_1")
        assert ann["evidence_id"] == "E-ANN-001"
        assert ann["annotation_type"] == "note"
        anns = get_annotations("E-ANN-001")
        assert len(anns) == 1

    def test_api_annotations(self):
        resp = client.post("/investigation-intel/annotations", json={
            "evidence_id": "E-API-ANN", "annotation_type": "highlight",
            "content": "Suspicious region", "tags": ["visual-artifact"],
        })
        assert resp.status_code == 200
        resp = client.get("/investigation-intel/annotations/E-API-ANN")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ============================================================
#  INVESTIGATION COPILOT
# ============================================================

class TestCopilot:
    def test_answer_supporting(self):
        from backend.services.copilot_service import answer_question
        evidence = [{"id": "E1", "category": "POSITIVE", "score": 0.8, "type": "model", "source_module": "image"}]
        result = answer_question("What evidence supports the assessment?", evidence=evidence)
        assert "answer" in result
        assert "citations" in result

    def test_answer_missing_info(self):
        from backend.services.copilot_service import answer_question
        result = answer_question("What information is missing?", evidence=[], analyses=[])
        assert "missing" in result["answer"].lower() or "key" in result["answer"].lower()

    def test_unsupported_question(self):
        from backend.services.copilot_service import answer_question
        result = answer_question("What is the weather today?")
        assert "answer" in result

    def test_api_copilot(self):
        resp = client.post("/investigation-intel/copilot", json={
            "question": "What evidence supports the assessment?",
            "evidence": [{"id": "E1", "category": "POSITIVE", "score": 0.8, "type": "model", "source_module": "image"}],
        })
        assert resp.status_code == 200
        assert "answer" in resp.json()


# ============================================================
#  REVIEW READINESS
# ============================================================

class TestReviewReadiness:
    def test_ready(self):
        from backend.services.review_service import compute_review_readiness
        result = compute_review_readiness(
            evidence_count=5, has_provenance=True, has_fact_check=True,
            has_source_analysis=True, conflict_count=0,
        )
        assert result["ready_for_review"] is True
        assert result["readiness_score"] >= 80

    def test_not_ready(self):
        from backend.services.review_service import compute_review_readiness
        result = compute_review_readiness(evidence_count=0)
        assert result["ready_for_review"] is False

    def test_api_readiness(self):
        resp = client.post("/investigation-intel/review-readiness", json={
            "evidence_count": 3, "has_provenance": True,
        })
        assert resp.status_code == 200
        assert "readiness_score" in resp.json()


# ============================================================
#  COMPLETENESS CHECKLIST
# ============================================================

class TestCompleteness:
    def test_complete(self):
        from backend.services.review_service import check_investigation_completeness
        result = check_investigation_completeness(
            has_media_analyzed=True, has_claims_extracted=True,
            has_sources_reviewed=True, has_provenance_checked=True,
            has_evidence_reviewed=True, has_conflicts_reviewed=True,
            has_uncertainty_assessed=True, has_model_versions_recorded=True,
            has_human_review=True, has_final_assessment=True,
        )
        assert result["is_complete"] is True
        assert result["completion_pct"] == 100.0

    def test_incomplete(self):
        from backend.services.review_service import check_investigation_completeness
        result = check_investigation_completeness(has_media_analyzed=True)
        assert result["is_complete"] is False
        assert len(result["missing_items"]) >= 8

    def test_api_completeness(self):
        resp = client.post("/investigation-intel/completeness", json={
            "has_media_analyzed": True, "has_final_assessment": True,
        })
        assert resp.status_code == 200
        assert "is_complete" in resp.json()


# ============================================================
#  OVERRIDE TRACKING
# ============================================================

class TestOverrideTracking:
    def test_track_and_get(self):
        from backend.services.review_service import track_override, get_overrides
        override = track_override(
            case_id="CASE-OVR", previous_assessment="High Risk",
            new_assessment="Inconclusive", reviewer="reviewer_1",
            reason="Insufficient provenance",
        )
        assert override["previous_assessment"] == "High Risk"
        assert override["new_assessment"] == "Inconclusive"
        overrides = get_overrides("CASE-OVR")
        assert len(overrides) == 1

    def test_api_overrides(self):
        resp = client.post("/investigation-intel/overrides", json={
            "case_id": "CASE-API-OVR", "previous_assessment": "Low",
            "new_assessment": "Review Needed", "reviewer": "r1",
            "reason": "New evidence",
        })
        assert resp.status_code == 200
        resp = client.get("/investigation-intel/overrides/CASE-API-OVR")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ============================================================
#  OVERCLAIM VALIDATOR
# ============================================================

class TestOverclaimValidator:
    def test_detects_overclaims(self):
        from backend.services.overclaim_validator import validate_assessment_language
        result = validate_assessment_language("High Risk", "This is definitely fake and proves manipulation", 85)
        assert result["language_valid"] is False
        assert result["overclaim_check"]["has_overclaims"] is True

    def test_clean_language(self):
        from backend.services.overclaim_validator import validate_assessment_language
        result = validate_assessment_language("High Risk", "Evidence indicates elevated manipulation risk", 85)
        assert result["language_valid"] is True

    def test_api_validate(self):
        resp = client.post("/investigation-intel/validate-language", json={
            "verdict": "High Risk", "explanation": "This is definitely fake",
            "risk_score": 85,
        })
        assert resp.status_code == 200
        assert "language_valid" in resp.json()
