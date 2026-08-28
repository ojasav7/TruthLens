"""Tests for all gap-fill features."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# ============================================================
#  AUTH
# ============================================================

class TestAuth:
    def test_login_success(self):
        resp = client.post("/platform/auth/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_failure(self):
        resp = client.post("/platform/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_register_and_login(self):
        resp = client.post("/platform/auth/register", json={
            "username": "testuser_gap", "password": "pass123", "role": "analyst"
        })
        assert resp.status_code == 200
        resp = client.post("/platform/auth/login", json={"username": "testuser_gap", "password": "pass123"})
        assert resp.status_code == 200

    def test_register_duplicate(self):
        client.post("/platform/auth/register", json={"username": "dup_user", "password": "p"})
        resp = client.post("/platform/auth/register", json={"username": "dup_user", "password": "p"})
        assert resp.status_code == 409

    def test_auth_me_unauthenticated(self):
        resp = client.get("/platform/auth/me")
        assert resp.json()["authenticated"] is False

    def test_auth_me_authenticated(self):
        from backend.services.auth_service import create_token
        token = create_token("test_user", "admin")
        resp = client.get("/platform/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.json()["authenticated"] is True
        assert resp.json()["role"] == "admin"

    def test_token_expiry(self):
        from backend.services.auth_service import TokenPayload, verify_token
        import time
        tp = TokenPayload(user_id="x", role="viewer", iat=time.time() - 99999, exp=time.time() - 1)
        assert tp.is_expired() is True

    def test_api_auth_unit(self):
        from backend.services.auth_service import create_token, verify_token
        token = create_token("user1", "analyst", "org1")
        payload = verify_token(token)
        assert payload is not None
        assert payload.user_id == "user1"
        assert payload.role == "analyst"


# ============================================================
#  WEBHOOKS
# ============================================================

class TestWebhooks:
    def test_register_and_list(self):
        resp = client.post("/platform/webhooks", json={
            "name": "Test Slack", "url": "https://hooks.slack.com/test", "platform": "slack",
        })
        assert resp.status_code == 200
        wh_id = resp.json()["id"]
        resp = client.get("/platform/webhooks")
        assert len(resp.json()) >= 1
        client.delete(f"/platform/webhooks/{wh_id}")

    def test_delete_webhook(self):
        resp = client.post("/platform/webhooks", json={
            "name": "Del Test", "url": "https://example.com/hook", "platform": "discord",
        })
        wh_id = resp.json()["id"]
        resp = client.delete(f"/platform/webhooks/{wh_id}")
        assert resp.status_code == 200

    def test_format_slack(self):
        from backend.services.webhook_integrations import _format_slack
        result = _format_slack("alert", {"verdict": "High Risk", "threat_score": 85, "message": "test"})
        assert "blocks" in result

    def test_format_discord(self):
        from backend.services.webhook_integrations import _format_discord
        result = _format_discord("alert", {"verdict": "Low", "threat_score": 15})
        assert "embeds" in result


# ============================================================
#  SOCIAL MONITOR
# ============================================================

class TestSocialMonitor:
    def test_add_and_list(self):
        from backend.services.social_monitor import add_url_to_monitor, list_monitored_urls
        entry = add_url_to_monitor({"url": "https://twitter.com/test"})
        assert entry["id"]
        urls = list_monitored_urls()
        assert len(urls) >= 1

    def test_detect_platform(self):
        from backend.services.social_monitor import detect_platform
        assert "twitter" in detect_platform("https://twitter.com/user/status/123")
        assert "youtube" in detect_platform("https://youtube.com/watch?v=abc")
        assert "reddit" in detect_platform("https://reddit.com/r/news")

    def test_alert_generation(self):
        from backend.services.social_monitor import add_url_to_monitor, record_scan_result, get_alerts
        entry = add_url_to_monitor({"url": "https://test.com", "alert_threshold": 0.5})
        alert = record_scan_result(entry["id"], 0.85, "High Risk")
        assert alert is not None
        assert alert["severity"] == "HIGH"

    def test_api_monitor(self):
        resp = client.post("/platform/monitor", json={"url": "https://example.com"})
        assert resp.status_code == 200
        resp = client.get("/platform/monitor")
        assert resp.status_code == 200

    def test_api_alerts(self):
        resp = client.get("/platform/alerts")
        assert resp.status_code == 200


# ============================================================
#  GDPR
# ============================================================

class TestGDPR:
    def test_submit_access_request(self):
        from backend.services.gdpr_service import submit_data_request
        result = submit_data_request("access", "subject_001")
        assert result["status"] == "pending"

    def test_process_erasure(self):
        from backend.services.gdpr_service import process_erasure_request
        result = process_erasure_request("subject_002")
        assert result["status"] == "completed"
        assert "erased" in result

    def test_consent(self):
        from backend.services.gdpr_service import record_consent, check_consent
        record_consent("s3", "analytics", True)
        assert check_consent("s3", "analytics") is True
        assert check_consent("s3", "marketing") is False

    def test_api_gdpr(self):
        resp = client.post("/platform/gdpr/request", json={
            "request_type": "access", "subject_id": "api_test",
        })
        assert resp.status_code == 200
        resp = client.get("/platform/gdpr/requests")
        assert resp.status_code == 200


# ============================================================
#  PROMETHEUS METRICS
# ============================================================

class TestMetrics:
    def test_prometheus_format(self):
        from backend.services.prometheus_metrics import render_prometheus_metrics, record_request
        record_request("/test", "GET", 200, 15.3)
        output = render_prometheus_metrics()
        assert "truthlens_uptime_seconds" in output
        assert "truthlens_requests_total" in output

    def test_api_metrics(self):
        resp = client.get("/platform/metrics")
        assert resp.status_code == 200
        assert "truthlens_uptime_seconds" in resp.text

    def test_api_metrics_json(self):
        resp = client.get("/platform/metrics/json")
        assert resp.status_code == 200
        assert "uptime_seconds" in resp.json()


# ============================================================
#  FORENSIC REPORTS
# ============================================================

class TestForensicReport:
    def test_generate_report(self):
        from backend.services.forensic_report import generate_forensic_report
        report = generate_forensic_report(
            analysis={"id": "A-001", "threat_score": 75, "verdict": "High Risk", "input_types": ["text"]},
            evidence=[{"id": "E1", "type": "model", "source_module": "nlp", "score": 0.8, "category": "NEGATIVE", "description": "Suspicious"}],
        )
        assert "report_id" in report
        assert "report_hash" in report
        assert report["digital_signature"]["algorithm"] == "HMAC-SHA256"
        assert len(report["limitations"]) >= 2

    def test_api_forensic_report(self):
        resp = client.post("/platform/forensic-report", json={
            "analysis": {"id": "A-002", "threat_score": 45, "verdict": "Review Needed", "input_types": ["image"]},
        })
        assert resp.status_code == 200
        assert "report_hash" in resp.json()


# ============================================================
#  DEPLOYMENT INFO
# ============================================================

class TestDeployment:
    def test_deployment_info(self):
        resp = client.get("/platform/deployment/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert data["features"]["jwt_auth"] is True
        assert data["features"]["forensic_reports"] is True


# ============================================================
#  API USAGE / RATE LIMITING
# ============================================================

class TestApiUsage:
    def test_rate_limit_check(self):
        from backend.services.api_usage import check_rate_limit, register_api_key, record_request
        register_api_key("test_hash", "test_key", rate_limit=5)
        for _ in range(3):
            record_request("test_hash", "/test")
        result = check_rate_limit("test_hash")
        assert result["allowed"] is True
        assert result["current"] == 3
        assert result["remaining"] == 2

    def test_rate_limit_exceeded(self):
        from backend.services.api_usage import check_rate_limit, register_api_key, record_request
        register_api_key("limit_hash", "limit_key", rate_limit=2)
        record_request("limit_hash", "/test")
        record_request("limit_hash", "/test")
        result = check_rate_limit("limit_hash")
        assert result["allowed"] is False
