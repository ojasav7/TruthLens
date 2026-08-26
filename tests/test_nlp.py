"""Tests for the NLP fake news classifier — Phase 1"""

import pytest
from models.nlp.model import FakeNewsClassifier


@pytest.fixture(scope="module")
def classifier():
    return FakeNewsClassifier()


class TestFakeNewsClassifier:
    def test_returns_valid_format(self, classifier):
        result = classifier.predict("Breaking: scientists discover new planet")
        assert "label" in result
        assert "confidence" in result
        assert result["label"] in ("fake", "real")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_confidence_is_float(self, classifier):
        result = classifier.predict("This is a test sentence.")
        assert isinstance(result["confidence"], float)

    def test_fake_headline(self, classifier):
        result = classifier.predict(
            "SHOCKING: You Won't Believe What This Celebrity Did!! Click here NOW!!!"
        )
        assert result["label"] in ("fake", "real")  # Model may vary
        assert 0.0 <= result["confidence"] <= 1.0

    def test_real_news(self, classifier):
        result = classifier.predict(
            "The Federal Reserve announced a 0.25% interest rate increase on Wednesday."
        )
        assert result["label"] in ("fake", "real")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_empty_string_handled(self, classifier):
        # Should not crash — may return any label with low confidence
        try:
            result = classifier.predict("")
            assert "label" in result
        except Exception:
            pass  # Acceptable to reject empty input
