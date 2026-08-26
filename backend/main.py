"""
TruthLens — AI Multimodal Misinformation & Threat Detection Platform
FastAPI backend entrypoint.
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.db.database import engine, Base
from backend.routers import text, image, video, audio, analyze, stretch
from backend.services.model_loader import load_all_models

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load all ML models. Shutdown: cleanup."""
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load models once at startup (singleton pattern)
    load_all_models()
    print("[OK] All models loaded and DB initialized.")
    yield
    print("[Shutdown] TruthLens stopped.")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="TruthLens API",
    description="AI Multimodal Misinformation & Threat Detection Platform",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/", tags=["Health"])
@limiter.exempt
async def root():
    return {"status": "ok", "service": "TruthLens API", "version": "0.1.0"}


@app.get("/health", tags=["Health"])
@limiter.exempt
async def health():
    return {"status": "healthy"}
