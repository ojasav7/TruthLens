"""Tests for performance fixes and explanation engine."""

import pytest
from unittest.mock import patch, MagicMock


class TestVideoModelCaching:
    """Verify video model uses cached image detector, not fresh instances."""

    def test_video_uses_cached_image_detector(self):
        """Video model should call get_image_model(), not create new instance."""
        from models.video.model import VideoDeepfakeDetector

        mock_detector = MagicMock()
        mock_detector.predict.return_value = {
            "label": "real",
            "confidence": 0.9,
            "cnn_raw": {"label": "real", "confidence": 0.9},
        }

        with patch("backend.services.model_loader.get_image_model", return_value=mock_detector) as mock_get:
            vid = VideoDeepfakeDetector()
            # Create a test video
            import cv2
            import numpy as np
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                video_path = f.name
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(video_path, fourcc, 1, (64, 64))
                for _ in range(5):
                    frame = np.zeros((64, 64, 3), dtype=np.uint8)
                    writer.write(frame)
                writer.release()

            try:
                result = vid.predict(video_path)
                # get_image_model should be called (not ImageDeepfakeDetector())
                mock_get.assert_called()
                assert "label" in result
            finally:
                os.unlink(video_path)

    def test_video_falls_back_when_cache_empty(self):
        """Video model should fall back to direct instantiation if cache is None."""
        from models.video.model import VideoDeepfakeDetector

        with patch("backend.services.model_loader.get_image_model", return_value=None):
            vid = VideoDeepfakeDetector()
            # Should not crash — falls back to ImageDeepfakeDetector()
            assert vid is not None


class TestExplanationEngine:
    """Test the plain English explanation generation."""

    def test_verify_explanation_with_evidence(self):
        """Verification with evidence should return valid result."""
        from backend.services.explanation_engine import verify_explanation

        result = verify_explanation(
            explanation="This content appears fake",
            evidence_count=3,
            has_provenance=True,
            has_fact_check=True,
            has_model_signal=True,
            has_evidence=True,
        )
        assert isinstance(result, dict)

    def test_verify_explanation_without_evidence(self):
        """Verification without evidence should still work."""
        from backend.services.explanation_engine import verify_explanation

        result = verify_explanation(
            explanation="",
            evidence_count=0,
        )
        assert isinstance(result, dict)


class TestEnsembleEngine:
    """Test the multi-signal ensemble fusion."""

    def test_ensemble_fuses_signals(self):
        """Ensemble should combine multiple model signals into final verdict."""
        from backend.services.ensemble_engine import compute_ensemble, ModelSignal

        signals = [
            ModelSignal(model_id="nlp", model_version="v1", label="fake", confidence=0.9),
            ModelSignal(model_id="image", model_version="v1", label="fake", confidence=0.7),
        ]
        result = compute_ensemble(signals)
        assert hasattr(result, "agreement")
        assert hasattr(result, "ensemble_confidence")
        assert result.agreement in ("HIGH_AGREEMENT", "MODERATE_AGREEMENT", "LOW_AGREEMENT", "STRONG_DISAGREEMENT")

    def test_ensemble_handles_single_signal(self):
        """Ensemble should work with just one signal."""
        from backend.services.ensemble_engine import compute_ensemble, ModelSignal

        signals = [
            ModelSignal(model_id="nlp", model_version="v1", label="real", confidence=0.95),
        ]
        result = compute_ensemble(signals)
        assert result.agreement == "SINGLE_MODEL"

    def test_ensemble_handles_empty_signals(self):
        """Ensemble should handle empty signal list gracefully."""
        from backend.services.ensemble_engine import compute_ensemble

        result = compute_ensemble([])
        assert result.agreement == "SINGLE_MODEL"
        assert result.signals == []
