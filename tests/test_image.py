"""Tests for the image deepfake classifier — Phase 2"""

import pytest
import numpy as np
from PIL import Image

from models.image.model import ImageDeepfakeDetector


@pytest.fixture(scope="module")
def detector():
    return ImageDeepfakeDetector()


def _make_test_image(color=(128, 128, 128), size=(224, 224)):
    """Create a simple test image."""
    return Image.new("RGB", size, color)


class TestImageDeepfakeDetector:
    def test_returns_valid_format(self, detector):
        img = _make_test_image()
        result = detector.predict(img)
        assert "label" in result
        assert "confidence" in result
        assert result["label"] in ("fake", "real")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_accepts_pil_image(self, detector):
        img = _make_test_image(color=(255, 0, 0))
        result = detector.predict(img)
        assert isinstance(result, dict)

    def test_accepts_file_path(self, detector, tmp_path):
        img = _make_test_image()
        path = tmp_path / "test.png"
        img.save(str(path))
        result = detector.predict(str(path))
        assert "label" in result

    def test_handles_grayscale_input(self, detector):
        img = Image.new("L", (224, 224), 128).convert("RGB")
        result = detector.predict(img)
        assert "label" in result

    def test_explain_returns_heatmap(self, detector):
        import base64
        img = _make_test_image()
        result = detector.explain(img)
        assert "label" in result
        assert "heatmap_b64" in result
        assert len(result["heatmap_b64"]) > 0
        # Verify base64 decodes
        heatmap_bytes = base64.b64decode(result["heatmap_b64"])
        assert len(heatmap_bytes) > 100
