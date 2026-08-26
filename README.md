# 🔍 TruthLens

**AI Multimodal Misinformation & Threat Detection Platform**

TruthLens scores text, images, videos, and audio for authenticity/misinformation risk, then explains why — combining NLP, computer vision, and audio analysis with a fusion layer into a single threat score.

---

## Architecture

```
┌──────────────┐
│   Frontend   │  Streamlit Dashboard
│  (Phase 6)   │  Port 8501
└──────┬───────┘
       │ HTTP
┌──────▼───────┐
│   Backend    │  FastAPI + SQLAlchemy
│  (Phase 5)   │  Port 8000
└──────┬───────┘
       │
┌──────▼───────────────────────────────────┐
│              Fusion Layer                │
│  ┌─────┐ ┌───────┐ ┌───────┐ ┌───────┐ │
│  │ NLP │ │ Image │ │ Video │ │ Audio │ │
│  │ BERT │ │EffNet │ │CNN+LSTM│ │Wav2V2 │ │
│  └─────┘ └───────┘ └───────┘ └───────┘ │
└──────────────────────────────────────────┘
```

## Quick Start

### 1. Clone & setup

```bash
git clone <repo-url> truthlens
cd truthlens
cp .env.example .env
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
```

### 2. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Run the frontend

```bash
streamlit run frontend/streamlit_app.py
```

### 4. Test

```bash
pytest tests/ -v
```

### Docker (optional)

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/predict/text` | NLP fake news check |
| POST | `/predict/image` | Image deepfake check |
| POST | `/predict/video` | Video deepfake check |
| POST | `/predict/audio` | Audio voice clone check |
| POST | `/analyze` | Combined multimodal analysis |
| GET | `/analyses` | History list |
| GET | `/analyze/{id}/report` | Download PDF report |
| GET | `/docs` | Swagger API docs |

## Phases

- [x] Phase 0: Setup
- [x] Phase 1: NLP Model (BERT)
- [x] Phase 2: Image Model (EfficientNet-B4)
- [x] Phase 3: Video Model (CNN + LSTM)
- [x] Phase 4: Audio Model (Wav2Vec2)
- [x] Phase 5: Fusion + Backend API
- [x] Phase 6: Frontend Dashboard
- [ ] Phase 7: Reports + Explainability
- [ ] Phase 8: Stretch Features
- [ ] Phase 9: Hardening + Deployment
- [ ] Phase 10: Documentation

## License

For educational purposes.
