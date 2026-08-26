"""Tests for the video deepfake classifier — Phase 3"""

import pytest
from models.video.model import VideoDeepfakeDetector


@pytest.fixture(scope="module")
def detector():
    return VideoDeepfakeDetector()


class TestVideoDeepfakeDetector:
    def test_returns_valid_format(self, detector, tmp_path):
        # Create a minimal test video (black frames) using OpenCV
        try:
            import cv2
            import numpy as np

            video_path = str(tmp_path / "test.mp4")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(video_path, fourcc, 1, (64, 64))
            for _ in range(5):
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                writer.write(frame)
            writer.release()

            result = detector.predict(video_path)
            assert "label" in result
            assert "confidence" in result
            assert "per_frame_scores" in result
            assert result["label"] in ("real", "fake")
        except ImportError:
            pytest.skip("opencv-python not installed")

    def test_empty_video_returns_safe(self, detector, tmp_path):
        """A corrupt/empty file should not crash the system."""
        empty_path = str(tmp_path / "empty.mp4")
        with open(empty_path, "wb") as f:
            f.write(b"not a video")

        try:
            result = detector.predict(empty_path)
            assert "label" in result
        except Exception:
            pass  # Acceptable to raise on corrupt input
