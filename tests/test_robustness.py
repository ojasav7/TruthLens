"""Robustness test — verify predictions survive image recompression."""

import io
import pytest
from PIL import Image


def _recompress(img: Image.Image, quality: int) -> io.BytesIO:
    """Recompress image at given JPEG quality, return as BytesIO."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return buf


class TestImageRobustness:
    """Test that image predictions don't collapse under recompression."""

    def test_prediction_stable_across_qualities(self):
        """Same image at Q30, Q50, Q90 should produce same label."""
        from models.image.model import ImageDeepfakeDetector

        detector = ImageDeepfakeDetector()
        img = Image.new("RGB", (224, 224), (128, 128, 128))

        labels = []
        for q in [30, 50, 90]:
            buf = _recompress(img, q)
            result = detector.predict(Image.open(buf))
            labels.append(result["label"])

        # All recompressed versions should produce the same label
        assert len(set(labels)) == 1, f"Labels differ across qualities: {labels}"

    def test_confidence_within_bounds(self):
        """Confidence should stay within reasonable bounds across qualities."""
        from models.image.model import ImageDeepfakeDetector

        detector = ImageDeepfakeDetector()
        img = Image.new("RGB", (224, 224), (128, 128, 128))

        confidences = []
        for q in [30, 50, 90]:
            buf = _recompress(img, q)
            result = detector.predict(Image.open(buf))
            confidences.append(result["confidence"])

        # Confidence should not swing more than 30% across qualities
        assert max(confidences) - min(confidences) < 0.3, \
            f"Confidence swing too large: {confidences}"


class TestVideoRobustness:
    """Test that video predictions survive quality reduction."""

    def test_prediction_stable(self):
        """Video prediction returns valid format."""
        import cv2
        import numpy as np
        import tempfile
        from pathlib import Path
        from models.video.model import VideoDeepfakeDetector

        detector = VideoDeepfakeDetector()

        # Create test video using mktemp to avoid Windows locking
        path = Path(tempfile.mktemp(suffix=".mp4"))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, 10, (64, 64))
        for _ in range(10):
            writer.write(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
        writer.release()
        del writer  # Release file handle

        try:
            result = detector.predict(str(path))
            assert "label" in result
            assert "confidence" in result
        finally:
            path.unlink(missing_ok=True)
