"""Global error handlers and startup validation."""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("truthlens")


def register_error_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": str(exc.detail),
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error("Unhandled error [request_id=%s]: %s", request_id, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )


def validate_startup():
    """Validate critical env vars and paths at startup. Returns list of warnings."""
    warnings = []
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./truthlens.db")
    if "changeme" in os.getenv("SECRET_KEY", "changeme"):
        warnings.append("SECRET_KEY is default — change it in production")
    if "sqlite" in db_url and os.getenv("ENVIRONMENT", "development") == "production":
        warnings.append("SQLite is not recommended for production — use PostgreSQL")
    model_dir = os.getenv("MODEL_DIR", "./models")
    if not os.path.isdir(model_dir):
        warnings.append(f"MODEL_DIR '{model_dir}' does not exist")
    return warnings
