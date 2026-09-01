"""
TruthLens — AI Multimodal Misinformation & Threat Detection Platform
FastAPI backend entrypoint.
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.db.database import engine, Base
from backend.db import models, models_advanced, models_reliability  # noqa: F401 — register tables for create_all
from backend.routers import text, image, video, audio, analyze, stretch, investigations, cases, advanced, streaming, workspaces
from backend.routers import batch, dashboard, forensics, nextgen, investigation_intel, gap_fills
from backend.routers import advanced_features
from backend.middleware import RequestIDMiddleware, setup_logging
from backend.errors import register_error_handlers, validate_startup
try:
    from backend.services.model_loader import load_all_models
except ImportError:
    load_all_models = None  # torch not installed

# Load environment variables
load_dotenv()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate, load models, create DB tables. Shutdown: cleanup."""
    import logging
    _log = logging.getLogger("truthlens")

    # Startup validation
    for w in validate_startup():
        _log.warning("STARTUP: %s", w)

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Create indexes
    from backend.db.indexes import create_indexes
    await create_indexes()
    _log.info("[OK] Database initialized.")

    # Load models once at startup (singleton pattern)
    try:
        load_all_models()
        _log.info("[OK] All models loaded.")
    except ImportError:
        _log.warning("ML dependencies (torch/cv2) not installed — running without models.")
    yield
    _log.info("[Shutdown] TruthLens stopped.")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="TruthLens API",
    description="AI Multimodal Misinformation & Threat Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
register_error_handlers(app)

# Request ID + logging middleware
app.add_middleware(RequestIDMiddleware)

# CORS — restrict in production, open in dev
import os
_production = os.getenv("ENVIRONMENT", "development") == "production"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not _production else ["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(text.router, prefix="/predict", tags=["NLP"])
app.include_router(image.router, prefix="/predict", tags=["Image"])
app.include_router(video.router, prefix="/predict", tags=["Video"])
app.include_router(audio.router, prefix="/predict", tags=["Audio"])
app.include_router(analyze.router, tags=["Fusion"])
app.include_router(stretch.router, prefix="/stretch", tags=["Stretch Features"])
app.include_router(investigations.router)
app.include_router(cases.router)
app.include_router(advanced.router)
app.include_router(streaming.router)
app.include_router(workspaces.router)
app.include_router(batch.router)
app.include_router(dashboard.router)
app.include_router(forensics.router)
app.include_router(nextgen.router)
app.include_router(investigation_intel.router)
app.include_router(gap_fills.router)
app.include_router(advanced_features.router)


@app.get("/", tags=["Health"])
@limiter.exempt
async def root():
    return {"status": "ok", "service": "TruthLens API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
@limiter.exempt
async def health():
    return {"status": "healthy"}


@app.get("/performance", tags=["Research"])
@limiter.exempt
async def performance():
    from backend.services.performance_monitor import get_summary
    return get_summary()


@app.get("/features", tags=["Research"])
@limiter.exempt
async def features():
    from backend.config import flags
    return {k: getattr(flags, k) for k in dir(flags) if not k.startswith("_")}


# --- Public API Key Management ---
from pydantic import BaseModel as _BaseModel

class APIKeyCreate(_BaseModel):
    name: str
    org_id: str | None = None
    rate_limit: int = 100


@app.post("/api-keys", tags=["Public API"])
@limiter.exempt
async def create_key(body: APIKeyCreate):
    """Create a new API key for public API access."""
    from backend.services.apikey_service import create_api_key
    return await create_api_key(body.name, body.org_id, body.rate_limit)


@app.get("/api-keys", tags=["Public API"])
@limiter.exempt
async def list_keys(org_id: str | None = None):
    """List API keys."""
    from backend.services.apikey_service import list_api_keys
    return await list_api_keys(org_id)


@app.delete("/api-keys/{key_id}", tags=["Public API"])
@limiter.exempt
async def revoke_key(key_id: str):
    """Revoke an API key."""
    from backend.services.apikey_service import revoke_api_key
    return await revoke_api_key(key_id)


# --- Multilingual NLP ---
@app.post("/predict/text/multilingual", tags=["NLP"])
@limiter.exempt
async def predict_multilingual(text: str = None, body: dict | None = None):
    """Multilingual text prediction — auto-detects English/Hindi/Hinglish."""
    from backend.services.language_router import multilingual_nlp
    if body and "text" in body:
        text = body["text"]
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 10000:
        raise HTTPException(status_code=400, detail="Text too long (max 10000 chars)")
    return multilingual_nlp.predict(text)
