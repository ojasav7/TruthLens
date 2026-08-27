"""Structured logging and request ID middleware."""

import logging
import time
import uuid
import sys
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# --- Structured JSON-like logging ---
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        parts = [
            f"[{record.levelname}]",
            f"[{record.name}]",
            record.getMessage(),
        ]
        if hasattr(record, "request_id"):
            parts.insert(1, f"[{record.request_id}]")
        if record.exc_info and record.exc_info[0]:
            parts.append(self.formatException(record.exc_info))
        return " ".join(parts)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("truthlens")


# --- Request ID Middleware ---
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"

        logger.info(
            "%s %s → %d (%sms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
