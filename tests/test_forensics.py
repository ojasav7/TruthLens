"""Tests for the 8 new forensics & intelligence features."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── AI Text Detection ───────────────────────────────────────────
class TestAITextDetection:
    def test_detect_human_text(self, client):
        """Human-written text should have low AI confidence."""
        resp = client.post("/forensics/detect-ai-text", json={
            "text": "So I was walking down the street and this crazy thing happened. "
                    "My dog just randomly started chasing a squirrel and knocked over "
                    "a trash can. It was hilarious but also kinda embarrassing."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "is_ai_generated" in data
        assert "confidence" in data
        assert "signals" in data
        assert 0 <= data["confidence"] <= 1

    def test_detect_ai_text(self, client):
        """AI-generated text should have higher confidence."""
        resp = client.post("/forensics/detect-ai-text", json={
            "text": "Artificial intelligence has revolutionized numerous industries, "
                    "enabling unprecedented levels of automation and efficiency. "
                    "Machine learning algorithms can now process vast quantities of data "
                    "to extract meaningful insights and drive informed decision-making. "
                    "The integration of AI technologies continues to transform business "
                    "operations across diverse sectors, fundamentally reshaping how "
                    "organizations approach complex problem-solving initiatives."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "is_ai_generated" in data
        assert data["confidence"] > 0  # should detect some AI signals

    def test_empty_text(self, client):
        resp = client.post("/forensics/detect-ai-text", json={"text": ""})
        assert resp.status_code == 200
        assert resp.json()["confidence"] == 0.0

    def test_too_long_text(self, client):
        resp = client.post("/forensics/detect-ai-text", json={"text": "a" * 10001})
        assert resp.status_code == 400


# ── Image Forensics (ELA) ──────────────────────────────────────
class TestImageForensics:
    def test_ela_clean_image(self, client):
        """A clean JPEG image should have low ELA score."""
        import io
        from PIL import Image
        img = Image.new("RGB", (128, 128), (100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        resp = client.post("/forensics/image-forensics",
                          files={"file": ("clean.jpg", buf, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert "ela" in data
        assert "copy_move" in data
        assert "overall_score" in data
        assert "verdict" in data
        assert data["verdict"] in ("LIKELY_AUTHENTIC", "POSSIBLY_TAMPERED", "LIKELY_TAMPERED")

    def test_non_image_rejected(self, client):
        resp = client.post("/forensics/image-forensics",
                          files={"file": ("test.txt", b"not an image", "text/plain")})
        assert resp.status_code == 400


# ── C2PA Content Credentials ────────────────────────────────────
class TestC2PA:
    def test_parse_c2pa(self, client):
        import io
        from PIL import Image
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        resp = client.post("/forensics/c2pa",
                          files={"file": ("photo.jpg", buf, "image/jpeg")})
        assert resp.status_code == 200
        data = resp.json()
        assert "has_c2pa" in data
        assert "provenance" in data
        assert "sha256" in data
        assert "explanation" in data

    def test_non_image_rejected(self, client):
        resp = client.post("/forensics/c2pa",
                          files={"file": ("test.txt", b"text", "text/plain")})
        assert resp.status_code == 400


# ── Social Media URL Intelligence ───────────────────────────────
class TestURLIntelligence:
    def test_analyze_twitter_url(self, client):
        resp = client.post("/forensics/url-intelligence",
                          json={"url": "https://twitter.com/user/status/1234567890"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "Twitter/X"
        assert "Twitter" in " ".join(data["signals"])

    def test_analyze_reddit_url(self, client):
        resp = client.post("/forensics/url-intelligence",
                          json={"url": "https://reddit.com/r/news/comments/abc123"})
        assert resp.status_code == 200
        assert resp.json()["platform"] == "Reddit"

    def test_shortened_url(self, client):
        resp = client.post("/forensics/url-intelligence",
                          json={"url": "https://bit.ly/abc123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_shortened"] is True
        assert data["shortener"] == "bit.ly"

    def test_bot_signals(self, client):
        resp = client.post("/forensics/url-intelligence",
                          json={"url": "https://example.com/page?utm_source=twitter&ref=abc"})
        assert resp.status_code == 200
        assert len(resp.json()["bot_signals"]) >= 1

    def test_batch_urls(self, client):
        resp = client.post("/forensics/url-intelligence/batch", json={
            "urls": [
                "https://twitter.com/user/123",
                "https://reuters.com/article",
                "https://bit.ly/short",
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["count"] == 3
        assert len(resp.json()["results"]) == 3

    def test_batch_limit(self, client):
        resp = client.post("/forensics/url-intelligence/batch", json={
            "urls": [f"https://example.com/{i}" for i in range(21)]
        })
        assert resp.status_code == 400


# ── Watermark Detection ─────────────────────────────────────────
class TestWatermarkDetection:
    def test_detect_watermark(self, client):
        import io
        from PIL import Image
        import numpy as np
        # Create image with slightly biased LSBs (simulates watermark)
        arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        # Bias LSBs toward 0 (reduces entropy)
        arr[:, :, 0] = arr[:, :, 0] & 0xFE
        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        resp = client.post("/forensics/watermark",
                          files={"file": ("watermarked.png", buf, "image/png")})
        assert resp.status_code == 200
        data = resp.json()
        assert "watermark_detected" in data
        assert "confidence" in data
        assert "lsb_analysis" in data
        assert "spectral_analysis" in data


# ── Sentiment / Manipulation Detection ──────────────────────────
class TestManipulationDetection:
    def test_detect_fear_mongering(self, client):
        resp = client.post("/forensics/detect-manipulation", json={
            "text": "DANGER! CRISIS! The government is destroying our future! "
                    "This shocking threat will ruin everything!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["manipulation_score"] > 0
        assert data["tactic_count"] >= 1
        assert any(t["tactic"] == "fear_mongering" for t in data["tactics_found"])

    def test_detect_clickbait(self, client):
        resp = client.post("/forensics/detect-manipulation", json={
            "text": "You won't believe what happens next! "
                    "This one weird trick doctors don't want you to know!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tactic_count"] >= 1
        assert any(t["tactic"] == "urgency_clickbait" for t in data["tactics_found"])

    def test_clean_text(self, client):
        resp = client.post("/forensics/detect-manipulation", json={
            "text": "The quarterly report shows a 5% increase in revenue. "
                    " analysts expect continued growth in the next quarter."
        })
        assert resp.status_code == 200
        assert resp.json()["manipulation_score"] == 0.0

    def test_text_health_report(self, client):
        resp = client.post("/forensics/text-health", json={
            "text": "SHOCKING: Scientists say this dangerous secret is being hidden!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "trust_score" in data
        assert "health" in data
        assert "manipulation" in data
        assert "ai_detection" in data
        assert data["health"] in ("HEALTHY", "SUSPICIOUS", "UNTRUSTWORTHY")


# ── Webhook Notifications ───────────────────────────────────────
class TestWebhooks:
    def test_create_webhook(self, client):
        resp = client.post("/forensics/webhooks", json={
            "url": "https://example.com/webhook",
            "name": "Test webhook"
        })
        assert resp.status_code == 200
        assert "webhook_id" in resp.json()

    def test_list_webhooks(self, client):
        resp = client.get("/forensics/webhooks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_delete_webhook(self, client):
        resp = client.post("/forensics/webhooks", json={
            "url": "https://example.com/delete-me"
        })
        wh_id = resp.json()["webhook_id"]
        resp = client.delete(f"/forensics/webhooks/{wh_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"


# ── Evidence Chain of Custody ───────────────────────────────────
class TestCustody:
    def test_create_chain(self, client):
        resp = client.post("/forensics/custody", json={
            "evidence_id": "E-TEST-001",
            "description": "Initial evidence collected",
            "actor": "analyst1"
        })
        assert resp.status_code == 200
        assert resp.json()["chain_length"] == 1
        assert resp.json()["integrity"] == "VERIFIED"

    def test_add_entry(self, client):
        client.post("/forensics/custody", json={
            "evidence_id": "E-TEST-002", "description": "Created"
        })
        resp = client.post("/forensics/custody/entry", json={
            "evidence_id": "E-TEST-002",
            "action": "ACCESSED",
            "description": "Analyst reviewed evidence",
            "actor": "analyst2"
        })
        assert resp.status_code == 200
        assert resp.json()["chain_length"] == 2

    def test_verify_chain(self, client):
        client.post("/forensics/custody", json={
            "evidence_id": "E-TEST-003", "description": "Created"
        })
        resp = client.get("/forensics/custody/E-TEST-003/verify")
        assert resp.status_code == 200
        assert resp.json()["integrity"] == "VERIFIED"

    def test_get_chain(self, client):
        client.post("/forensics/custody", json={
            "evidence_id": "E-TEST-004", "description": "Created"
        })
        resp = client.get("/forensics/custody/E-TEST-004")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert data["chain_length"] >= 1

    def test_verify_missing_chain(self, client):
        resp = client.get("/forensics/custody/NONEXISTENT/verify")
        assert resp.status_code == 200
        assert resp.json()["integrity"] == "NOT_FOUND"
