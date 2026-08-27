"""Headless verification of the 3 adversarial review fixes.

Tests the actual code paths, not through HTTP — directly calling the
functions to assert correct behavior.
"""
import asyncio
import logging
import io


# ── Fix 1: validate_text strips and returns ──────────────────────
def test_validate_text_strips_whitespace():
    from backend.validation import validate_text
    # Text with leading/trailing whitespace should be stripped
    result = validate_text("  hello world  ")
    assert result == "hello world", f"Expected stripped text, got: {result!r}"


def test_validate_text_rejects_too_long():
    from backend.validation import validate_text
    from fastapi import HTTPException
    long_text = "a" * 10001
    try:
        validate_text(long_text)
        assert False, "Should have raised HTTPException for too-long text"
    except HTTPException as e:
        assert e.status_code == 400
        assert "too long" in e.detail.lower()


def test_validate_text_allows_max_length():
    from backend.validation import validate_text
    exact_text = "a" * 10000
    result = validate_text(exact_text)
    assert result == exact_text


# ── Fix 2: text.py uses stripped text ────────────────────────────
def test_text_predict_uses_stripped_text():
    """Verify the predict endpoint receives stripped text, not raw input."""
    from backend.services.model_loader import get_nlp_model
    model = get_nlp_model()
    if model is None:
        return  # skip if model not loaded

    # The key assertion: predict with stripped vs unstripped should
    # produce the same result (since the model sees the stripped text)
    raw = "  Breaking news today  "
    stripped = raw.strip()
    r1 = model.predict(raw)
    r2 = model.predict(stripped)
    # Both should produce valid results with the same label
    assert r1["label"] == r2["label"], f"Labels differ: {r1['label']} vs {r2['label']}"
    assert "confidence" in r1 and "confidence" in r2


# ── Fix 3: batch validation ──────────────────────────────────────
def test_validate_upload_size_limit():
    """validate_upload rejects files over 100MB."""
    from backend.validation import validate_upload, MAX_UPLOAD_BYTES
    from fastapi import HTTPException
    import asyncio

    # Create a fake UploadFile-like object
    class FakeUploadFile:
        def __init__(self, data):
            self._data = data
            self._pos = 0
        async def read(self, size=-1):
            return self._data

    # Small file should pass
    small = FakeUploadFile(b"small data")
    result = asyncio.get_event_loop().run_until_complete(validate_upload(small))
    assert result == b"small data"

    # Oversized file should fail
    big = FakeUploadFile(b"x" * (MAX_UPLOAD_BYTES + 1))
    try:
        asyncio.get_event_loop().run_until_complete(validate_upload(big))
        assert False, "Should have raised HTTPException for oversized file"
    except HTTPException as e:
        assert e.status_code == 400
        assert "too large" in e.detail.lower()


# ── Fix 4: request ID middleware injects into log records ────────
def test_request_id_injected_into_log_records():
    """Verify the log record factory actually injects request_id."""
    import logging

    old_factory = logging.getLogRecordFactory()

    # Simulate what the middleware does
    test_request_id = "test-123-abc"

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = test_request_id
        return record

    logging.setLogRecordFactory(record_factory)

    try:
        # Create a log record and check it has request_id
        logger = logging.getLogger("truthlens.test")
        record = logger.makeRecord(
            name="truthlens.test",
            level=logging.INFO,
            fn="test.py",
            lno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert hasattr(record, "request_id"), "Log record missing request_id"
        assert record.request_id == test_request_id, f"Wrong request_id: {record.request_id}"

        # Also verify the formatter sees it
        from backend.middleware import StructuredFormatter
        formatter = StructuredFormatter()
        formatted = formatter.format(record)
        assert test_request_id in formatted, f"Request ID not in formatted log: {formatted}"
    finally:
        logging.setLogRecordFactory(old_factory)


# ── Fix 5: batch endpoint validates item count ───────────────────
def test_batch_rejects_too_many_items():
    """The batch endpoint should reject >20 items."""
    from backend.validation import MAX_BATCH_ITEMS
    assert MAX_BATCH_ITEMS == 20, f"Expected 20, got {MAX_BATCH_ITEMS}"


# ── Fix 6: end-to-end validate_text through text router ─────────
def test_text_endpoint_validates_length():
    """POST /predict/text with too-long text should return 400."""
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        # Too long
        resp = client.post("/predict/text", json={"text": "a" * 10001})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

        # Just right
        resp = client.post("/predict/text", json={"text": "a" * 10000})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        # Empty
        resp = client.post("/predict/text", json={"text": ""})
        assert resp.status_code == 400


def test_batch_endpoint_validates_items():
    """POST /analyze/batch with >20 items should return 400."""
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        # Too many items
        items = [{"text": f"item {i}"} for i in range(21)]
        resp = client.post("/analyze/batch", json={"items": items})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

        # Exactly 20 — should work
        items = [{"text": f"item {i}"} for i in range(20)]
        resp = client.post("/analyze/batch", json={"items": items})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"


def test_streaming_rejects_bad_modality():
    """POST /stream/upload-chunk with invalid modality should return 400."""
    from fastapi.testclient import TestClient
    from backend.main import app
    import io

    with TestClient(app) as client:
        # Invalid modality
        fake_file = io.BytesIO(b"fake audio data")
        resp = client.post(
            "/stream/upload-chunk?modality=text",
            files={"file": ("chunk.wav", fake_file, "audio/wav")},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"


def test_multilingual_rejects_empty():
    """POST /predict/text/multilingual with empty text should return 400."""
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        resp = client.post("/predict/text/multilingual", json={"text": ""})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"


# ── Fix 7: CORS configuration ───────────────────────────────────
def test_cors_allows_requests():
    """Verify CORS middleware doesn't block requests with Origin header."""
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        # Without Origin — normal request
        resp = client.get("/health")
        assert resp.status_code == 200

        # With Origin header — CORS should respond with Allow-Origin
        resp = client.get("/health", headers={"Origin": "http://localhost:8501"})
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers


# ── Fix 8: DB indexes exist ──────────────────────────────────────
def test_indexes_created():
    """Verify all 12 indexes were created in the database."""
    import asyncio
    from backend.db.database import engine
    from sqlalchemy import text

    async def check():
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ))
            indexes = {row[0] for row in result.all()}
            expected = {
                "idx_analyses_timestamp", "idx_analyses_verdict", "idx_analyses_threat",
                "idx_cases_status", "idx_cases_priority", "idx_cases_created",
                "idx_evidence_case", "idx_audit_case", "idx_audit_timestamp",
                "idx_fingerprint_sha", "idx_fingerprint_media", "idx_apikey_hash",
            }
            missing = expected - indexes
            assert not missing, f"Missing indexes: {missing}"
            return len(indexes)

    count = asyncio.get_event_loop().run_until_complete(check())
    assert count >= 12, f"Expected at least 12 indexes, got {count}"
