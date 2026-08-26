"""Tests for the audio voice clone classifier — Phase 4"""

import pytest


class TestAudioDeepfakeDetector:
    def test_import(self):
        from models.audio.model import AudioDeepfakeDetector
        assert AudioDeepfakeDetector is not None

    def test_valid_format(self):
        """Test with a generated sine wave audio file."""
        try:
            import numpy as np
            import soundfile as sf
            from models.audio.model import AudioDeepfakeDetector
            import tempfile
            from pathlib import Path

            sr = 16000
            duration = 2.0
            t = np.linspace(0, duration, int(sr * duration))
            audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

            path = Path(tempfile.mktemp(suffix=".wav"))
            try:
                sf.write(str(path), audio, sr)
                detector = AudioDeepfakeDetector()
                result = detector.predict(str(path))
                assert "label" in result
                assert "confidence" in result
                assert result["label"] in ("real", "cloned")
                assert 0.0 <= result["confidence"] <= 1.0
            finally:
                path.unlink(missing_ok=True)
        except ImportError:
            pytest.skip("soundfile not installed")

    def test_explain(self):
        """Test explainability returns frequency-band attributions."""
        try:
            import numpy as np
            import soundfile as sf
            from models.audio.model import AudioDeepfakeDetector
            import tempfile
            from pathlib import Path

            sr = 16000
            audio = np.sin(2 * np.pi * 440 * np.linspace(0, 2, sr * 2)).astype(np.float32)

            path = Path(tempfile.mktemp(suffix=".wav"))
            try:
                sf.write(str(path), audio, sr)
                detector = AudioDeepfakeDetector()
                result = detector.explain(str(path))
                assert "label" in result
                assert "confidence" in result
                assert "top_coefficients" in result
                assert len(result["top_coefficients"]) > 0
                assert "mfcc_index" in result["top_coefficients"][0]
                assert "importance" in result["top_coefficients"][0]
            finally:
                path.unlink(missing_ok=True)
        except ImportError:
            pytest.skip("soundfile not installed")
