"""Integration tests for TruthLens API endpoints — Phase 5"""

import pytest
from fastapi.testclient import TestClient

# NOTE: These tests require the models to be loaded.
# For CI without GPU, mock the models in conftest.py.

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "TruthLens API"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestTextEndpoint:
    def test_predict_text(self, client):
        resp = client.post(
            "/predict/text",
            json={"text": "Breaking news: major event happens today"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "confidence" in data

    def test_predict_text_empty(self, client):
        resp = client.post("/predict/text", json={"text": ""})
        assert resp.status_code == 400

    def test_predict_text_explain(self, client):
        resp = client.post(
            "/predict/text/explain",
            json={"text": "SHOCKING: Government caught fabricating data!", "top_k": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "tokens" in data
        assert len(data["tokens"]) <= 5
        assert all("token" in t and "attribution" in t for t in data["tokens"])
        assert data["explained_output"] == "logits"


class TestAnalyzeEndpoint:
    def test_text_only(self, client):
        resp = client.post(
            "/analyze",
            data={"text": "Some suspicious news headline"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "threat_score" in data
        assert "verdict" in data
        assert "consistency" in data
        assert data["verdict"] in ("Low", "Review Needed", "High Risk")

    def test_no_input_rejected(self, client):
        resp = client.post("/analyze", data={})
        assert resp.status_code == 400

    def test_image_only(self, client):
        """Upload a small test image."""
        import io
        from PIL import Image

        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/analyze",
            files={"image": ("test.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "threat_score" in data
        assert "consistency" in data
        assert "image" in data.get("breakdown", {})

    def test_text_image_combo(self, client):
        """Test text + image fusion."""
        import io
        from PIL import Image

        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/analyze",
            data={"text": "Breaking: major discovery announced"},
            files={"image": ("test.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "threat_score" in data
        assert "text" in data.get("breakdown", {})
        assert "image" in data.get("breakdown", {})

    def test_text_video_combo(self, client):
        """Test text + video fusion."""
        import cv2
        import numpy as np
        import tempfile

        tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(tmp.name, fourcc, 10, (64, 64))
        for _ in range(10):
            writer.write(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        writer.release()

        with open(tmp.name, 'rb') as f:
            resp = client.post(
                "/analyze",
                data={"text": "Suspicious video circulating online"},
                files={"video": ("test.mp4", f, "video/mp4")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "threat_score" in data
        assert "text" in data.get("breakdown", {})
        assert "video" in data.get("breakdown", {})

    def test_fusion_consistency(self, client):
        """Verify consistency field is present in all responses."""
        resp = client.post(
            "/analyze",
            data={"text": "Another test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["consistency"] in ("unanimous", "mixed")


class TestVideoEndpoint:
    def test_predict_video(self, client):
        """Upload a small test video."""
        import cv2
        import numpy as np
        import tempfile

        # Create test video
        tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(tmp.name, fourcc, 10, (64, 64))
        for _ in range(10):
            writer.write(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        writer.release()

        with open(tmp.name, 'rb') as f:
            resp = client.post(
                "/predict/video",
                files={"file": ("test.mp4", f, "video/mp4")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "confidence" in data
        assert "per_frame_scores" in data

    def test_predict_video_explain(self, client):
        import cv2
        import numpy as np
        import tempfile

        tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(tmp.name, fourcc, 10, (64, 64))
        for _ in range(10):
            writer.write(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        writer.release()

        with open(tmp.name, 'rb') as f:
            resp = client.post(
                "/predict/video/explain",
                files={"file": ("test.mp4", f, "video/mp4")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "frame_importance" in data
        assert len(data["frame_importance"]) > 0


class TestImageEndpoint:
    def test_predict_image(self, client):
        import io
        from PIL import Image

        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/predict/image",
            files={"file": ("test.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "confidence" in data

    def test_predict_image_explain(self, client):
        import base64, io
        from PIL import Image

        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/predict/image/explain",
            files={"file": ("test.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "heatmap_b64" in data
        assert len(base64.b64decode(data["heatmap_b64"])) > 100


class TestAudioEndpoint:
    def test_predict_audio(self, client):
        import numpy as np
        import soundfile as sf
        import tempfile
        from pathlib import Path

        sr = 16000
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 2, sr * 2)).astype(np.float32)
        path = Path(tempfile.mktemp(suffix='.wav'))
        try:
            sf.write(str(path), audio, sr)
            with open(path, 'rb') as f:
                resp = client.post(
                    "/predict/audio",
                    files={"file": ("test.wav", f, "audio/wav")},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "label" in data
            assert "confidence" in data
        finally:
            path.unlink(missing_ok=True)

    def test_predict_audio_explain(self, client):
        import numpy as np
        import soundfile as sf
        import tempfile
        from pathlib import Path

        sr = 16000
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, 2, sr * 2)).astype(np.float32)
        path = Path(tempfile.mktemp(suffix='.wav'))
        try:
            sf.write(str(path), audio, sr)
            with open(path, 'rb') as f:
                resp = client.post(
                    "/predict/audio/explain",
                    files={"file": ("test.wav", f, "audio/wav")},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "label" in data
            assert "top_coefficients" in data
            assert len(data["top_coefficients"]) > 0
        finally:
            path.unlink(missing_ok=True)


class TestAnalysesEndpoint:
    def test_list_analyses(self, client):
        resp = client.get("/analyses?limit=5")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestInvestigationsEndpoint:
    def test_create_and_get_investigation(self, client):
        # First create an analysis
        resp = client.post("/analyze", data={"text": "Test for investigation"})
        assert resp.status_code == 200
        analysis_id = resp.json()["id"]

        # Create investigation
        resp = client.post(f"/investigations/{analysis_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "case_id" in data
        assert data["status"] == "OPEN"
        assert data["evidence_count"] > 0

        # Get investigation
        case_id = data["case_id"]
        resp = client.get(f"/investigations/{case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == case_id
        assert len(data["evidence"]) > 0
        assert len(data["audit_trail"]) > 0
        assert "strength" in data
        assert "agreement" in data

    def test_get_audit_trail(self, client):
        resp = client.post("/analyze", data={"text": "Audit trail test"})
        analysis_id = resp.json()["id"]
        resp = client.post(f"/investigations/{analysis_id}")
        case_id = resp.json()["case_id"]

        resp = client.get(f"/investigations/{case_id}/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["events"]) > 0
        assert data["events"][0]["event_type"] == "CASE_CREATED"

    def test_investigation_not_found(self, client):
        resp = client.get("/investigations/nonexistent")
        assert resp.status_code == 404

    def test_investigation_has_cross_modal_and_explanation(self, client):
        resp = client.post("/analyze", data={"text": "Cross-modal test"})
        analysis_id = resp.json()["id"]
        resp = client.post(f"/investigations/{analysis_id}")
        case_id = resp.json()["case_id"]

        resp = client.get(f"/investigations/{case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "cross_modal_analysis" in data
        assert "explanation" in data
        assert "category" in data["explanation"]
        assert data["explanation"]["category"] in ("WHY_FLAGGED", "WHY_NOT_FLAGGED", "WHAT_REQUIRES_REVIEW")

    def test_video_timeline_endpoint(self, client):
        resp = client.get("/investigations/nonexistent/timeline")
        assert resp.status_code == 404


class TestCaseManagement:
    def test_create_and_list_cases(self, client):
        resp = client.post("/cases", json={"title": "Test Case", "description": "Testing case mgmt"})
        assert resp.status_code == 200
        case_id = resp.json()["case_id"]

        resp = client.get("/cases")
        assert resp.status_code == 200
        assert any(c["case_id"] == case_id for c in resp.json())

    def test_get_case(self, client):
        resp = client.post("/cases", json={"title": "Get Test"})
        case_id = resp.json()["case_id"]

        resp = client.get(f"/cases/{case_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Test"
        assert resp.json()["status"] == "OPEN"

    def test_submit_review(self, client):
        resp = client.post("/cases", json={"title": "Review Test"})
        case_id = resp.json()["case_id"]

        resp = client.post(f"/cases/{case_id}/review", json={
            "reviewer_id": "reviewer1",
            "verdict": "MANIPULATED",
            "notes": "Confirmed fake"
        })
        assert resp.status_code == 200
        assert resp.json()["verdict"] == "MANIPULATED"

        # Case should be resolved
        resp = client.get(f"/cases/{case_id}")
        assert resp.json()["status"] == "RESOLVED"
        assert len(resp.json()["reviews"]) == 1

    def test_invalid_review_verdict(self, client):
        resp = client.post("/cases", json={"title": "Bad Review"})
        case_id = resp.json()["case_id"]

        resp = client.post(f"/cases/{case_id}/review", json={
            "reviewer_id": "r1", "verdict": "INVALID"
        })
        assert resp.status_code == 400


class TestClaimExtraction:
    def test_extract_claims(self, client):
        resp = client.post("/stretch/claims", json={
            "text": "Scientists discovered a new species. The government announced new policies. Climate change is accelerating."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "claims" in data
        assert data["count"] >= 2
        assert all("id" in c and "text" in c for c in data["claims"])

    def test_extract_claims_empty(self, client):
        resp = client.post("/stretch/claims", json={"text": ""})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestResearchEndpoints:
    def test_performance_endpoint(self, client):
        resp = client.get("/performance")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_features_endpoint(self, client):
        resp = client.get("/features")
        assert resp.status_code == 200
        data = resp.json()
        assert "INVESTIGATION_MODE" in data
        assert "CONTRADICTION_ENGINE" in data
        assert all(isinstance(v, bool) for v in data.values())


class TestAdvancedFeatures:
    # #27 Media Fingerprint
    def test_fingerprint(self, client):
        import io
        from PIL import Image
        img = Image.new("RGB", (32, 32), (100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        resp = client.post("/advanced/fingerprint", files={"file": ("test.png", buf, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert "media_id" in data
        assert data["media_id"].startswith("TL-M-")
        assert "sha256" in data

    # #28 History filters
    def test_analyses_filters(self, client):
        resp = client.get("/analyses?limit=5&verdict=Low")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_cases_filters(self, client):
        resp = client.get("/cases?limit=5&priority=MEDIUM")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    # #19 Evidence Graph
    def test_evidence_graph(self, client):
        resp = client.post("/analyze", data={"text": "Graph test"})
        analysis_id = resp.json()["id"]
        resp = client.post(f"/investigations/{analysis_id}")
        case_id = resp.json()["case_id"]
        resp = client.get(f"/advanced/graph/{case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["node_count"] > 0

    # #46 Auto-prioritization
    def test_investigation_has_priority(self, client):
        resp = client.post("/analyze", data={"text": "Priority test"})
        analysis_id = resp.json()["id"]
        resp = client.post(f"/investigations/{analysis_id}")
        data = resp.json()
        assert "priority" in data
        assert data["priority"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # #35 Robustness Lab
    def test_robustness_lab(self, client):
        import io
        from PIL import Image
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        resp = client.post("/advanced/robustness", files={"file": ("test.png", buf, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert "robustness_score" in data
        assert "transformations" in data
        assert "original_label" in data

    # #36 Model Benchmark
    def test_benchmarks(self, client):
        resp = client.get("/advanced/benchmarks")
        assert resp.status_code == 200
        data = resp.json()
        assert "nlp" in data or "image" in data

    def test_model_versions(self, client):
        resp = client.get("/advanced/models/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert "nlp" in data
        assert data["nlp"]["version"] == "1.0.0"

    # #38 Confidence Calibration
    def test_calibration(self, client):
        resp = client.get("/advanced/calibration")
        assert resp.status_code == 200
        assert "buckets" in resp.json()

    # #39 Misinformation Radar
    def test_radar(self, client):
        resp = client.get("/advanced/radar")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_analyses" in data
        assert "risk_distribution" in data
        assert data["total_analyses"] > 0

    # #58 Explain Like I'm Human
    def test_explain_human(self, client):
        resp = client.post("/analyze", data={"text": "Human explain test"})
        analysis_id = resp.json()["id"]
        resp = client.post(f"/investigations/{analysis_id}")
        case_id = resp.json()["case_id"]
        resp = client.get(f"/advanced/explain-human/{case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "plain_english_summary" in data
        assert "plain_english_reasons" in data
        assert "technical_available" in data

    # #33 Source Credibility (via stretch)
    def test_credibility_endpoint(self, client):
        resp = client.post("/stretch/credibility", json={"url": "https://reuters.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["credibility"] == "high"
        assert data["risk_score"] < 0.5
