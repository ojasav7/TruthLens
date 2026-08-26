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
