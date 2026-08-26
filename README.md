# TruthLens

**Explainable Multimodal Misinformation & Synthetic-Media Investigation Platform**

TruthLens analyzes text, images, video, and audio, combines independent AI signals with provenance, fact-checking, source intelligence, and cross-modal consistency analysis, and produces an evidence-backed risk assessment with human-review and audit capabilities.

[![Tests](https://github.com/ojasav7/TruthLens/actions/workflows/ci.yml/badge.svg)](https://github.com/ojasav7/TruthLens/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Architecture

```
                         ┌─────────────────────────┐
                         │    Streamlit Dashboard   │  :8501
                         │    (frontend/)           │
                         └──────────┬──────────────┘
                                    │ HTTP
                         ┌──────────▼──────────────┐
                         │     FastAPI Backend       │  :8000
                         │     (backend/)            │
                         └──────────┬──────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
  ┌──────▼───────┐  ┌──────────────▼──────────┐  ┌───────────▼──────────┐
  │  /predict/   │  │     /analyze (fusion)    │  │  /investigations     │
  │  text/image/ │  │  Weighted ensemble +     │  │  Evidence engine +   │
  │  video/audio │  │  calibration + consistency│  │  Contradiction +     │
  └──────┬───────┘  └──────────┬───────────────┘  │  Explanation         │
         │                     │                   └───────────┬──────────┘
         │                     │                               │
         │           ┌─────────▼───────────┐     ┌────────────▼─────────┐
         │           │   4 ML Models        │     │   Case Management    │
         │           │   DistilBERT         │     │   Human Review       │
         │           │   EfficientNet-B4    │     │   Audit Trail        │
         │           │   MobileNetV2+LSTM   │     └──────────────────────┘
         │           │   MFCC+MLP           │
         │           └─────────────────────┘
         │
  ┌──────▼──────────────────────────────────┐
  │  Stretch Features                       │
  │  OCR · EXIF · Credibility · Screenshot │
  │  Claim Extraction · Robustness Lab     │
  └─────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy (async), SQLite, SlowAPI rate limiting |
| **NLP** | DistilBERT (HuggingFace Transformers), SHAP explainability |
| **Image** | EfficientNet-B4 (timm), Grad-CAM heatmaps |
| **Video** | MobileNetV2 + LSTM, OpenCV frame extraction |
| **Audio** | MFCC features + MLP (torchaudio), frequency-band explanations |
| **Fusion** | Weighted ensemble with dynamic renormalization + confidence calibration |
| **Investigation** | Evidence engine, contradiction detection, explanation engine |
| **Frontend** | Streamlit dashboard with Plotly gauges and charts |
| **Infra** | Docker Compose, pytest, GitHub Actions CI |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Git
- (Optional) Docker + Docker Compose

### 1. Clone and setup

```bash
git clone https://github.com/ojasav7/TruthLens.git
cd TruthLens
cp .env.example .env

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Generate training data

```bash
python data/scripts/generate_nlp_data.py
python data/scripts/generate_image_data.py
python data/scripts/generate_video_data.py
python data/scripts/generate_audio_data.py
```

### 3. Train models

```bash
python -m models.nlp.train_fast     # ~2 min CPU
python -m models.image.train        # ~5 min CPU
python -m models.video.train        # ~3 min CPU
python -m models.audio.train        # ~5 sec CPU
```

### 4. Start the API

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs at **http://localhost:8000/docs** (Swagger UI).

### 5. Start the dashboard

```bash
streamlit run frontend/streamlit_app.py
```

Dashboard at **http://localhost:8501**.

### 6. Run tests

```bash
pytest tests/ -v    # 49 tests
```

### Docker

```bash
docker-compose up --build
```

---

## API Reference (29 Endpoints)

### Health & Research

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/performance` | Analysis timing metrics |
| GET | `/features` | Feature flag status |

### Per-Modality Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict/text` | NLP fake news classification |
| POST | `/predict/text/explain` | Text + SHAP token attributions |
| POST | `/predict/image` | Image deepfake classification |
| POST | `/predict/image/explain` | Image + Grad-CAM heatmap |
| POST | `/predict/video` | Video deepfake + per-frame scores |
| POST | `/predict/video/explain` | Video + frame importance |
| POST | `/predict/audio` | Voice clone classification |
| POST | `/predict/audio/explain` | Audio + MFCC attributions |

### Unified Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Multimodal analysis (any combination) |
| GET | `/analyses` | List recent analyses |
| GET | `/analyze/{id}/report` | Download PDF report |

### Investigation Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/investigations/{analysis_id}` | Create investigation from analysis |
| GET | `/investigations/{case_id}` | Full investigation + evidence + explanation |
| GET | `/investigations/{case_id}/audit` | Chronological audit trail |
| GET | `/investigations/{case_id}/timeline` | Video suspicious segments |
| POST | `/investigations/{case_id}/reanalyze` | Re-analysis (versioned) |

### Case Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List cases (filterable) |
| POST | `/cases` | Create investigation case |
| GET | `/cases/{case_id}` | Get case with reviews |
| POST | `/cases/{case_id}/review` | Submit human review |

### Stretch Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/stretch/ocr` | Extract text from images |
| POST | `/stretch/exif` | Analyze image metadata |
| POST | `/stretch/credibility` | Score URL credibility |
| POST | `/stretch/screenshot` | Screenshot → OCR → claims |
| POST | `/stretch/claims` | Extract individual claims |

---

## Threat Scoring

| Score | Verdict | Meaning |
|-------|---------|---------|
| 0–30 | **Low** | Content appears authentic |
| 31–70 | **Review Needed** | Mixed signals, human review recommended |
| 71–100 | **High Risk** | Strong indicators of manipulation |

Fusion weights: text (25%), image (25%), video (35%), audio (15%). Weights renormalize when not all modalities are present. Confidence scores are Platt-calibrated. Cross-modal disagreement adds a boost of up to 15 points.

---

## Investigation Flow

```
Upload → Analyze → Create Investigation → Collect Evidence
    → Cross-Modal Analysis → Contradiction Detection
    → Human-readable Explanation → Risk Assessment
    → Human Review (if needed) → Case Resolution → Report
```

Each investigation includes:
- **Evidence Ledger** — structured records from each modality
- **Cross-Modal Analysis** — detects when modalities disagree
- **Explanation** — human-readable reasons (not raw model internals)
- **Audit Trail** — chronological event history
- **Model Versions** — tracks which model made each prediction

---

## Project Structure

```
TruthLens/
├── backend/
│   ├── main.py                      # FastAPI app + lifespan + rate limiting
│   ├── config.py                    # Feature flags (13 toggleable modules)
│   ├── schemas.py                   # Shared Pydantic models
│   ├── requirements.txt
│   ├── db/
│   │   ├── database.py              # Async SQLAlchemy engine
│   │   ├── models.py                # Analysis ORM model
│   │   └── models_advanced.py       # Investigation, Evidence, Audit, Review models
│   ├── routers/
│   │   ├── text.py                  # POST /predict/text[/explain]
│   │   ├── image.py                 # POST /predict/image[/explain]
│   │   ├── video.py                 # POST /predict/video[/explain]
│   │   ├── audio.py                 # POST /predict/audio[/explain]
│   │   ├── analyze.py               # POST /analyze, GET /analyses
│   │   ├── stretch.py               # OCR, EXIF, credibility, screenshot, claims
│   │   ├── investigations.py        # Investigation CRUD + timeline + reanalyze
│   │   └── cases.py                 # Case management + human review
│   └── services/
│       ├── model_loader.py          # Singleton model loading
│       ├── report_service.py        # PDF generation (ReportLab)
│       ├── evidence_engine.py       # Evidence collection + strength/agreement
│       ├── investigation_service.py # Investigation CRUD
│       ├── audit_service.py         # Audit trail logging
│       ├── contradiction_engine.py  # Cross-modal disagreement detection
│       ├── video_timeline.py        # Suspicious segment grouping
│       ├── explanation_engine.py    # Human-readable explanations
│       ├── claim_extractor.py       # Text → individual claims
│       ├── screenshot_service.py    # Screenshot → OCR → claims
│       ├── performance_monitor.py   # Timing metrics
│       ├── ocr_service.py           # Tesseract OCR
│       ├── exif_service.py          # EXIF metadata analysis
│       └── credibility_service.py   # URL credibility scoring
├── models/
│   ├── nlp/                         # DistilBERT + SHAP
│   ├── image/                       # EfficientNet-B4 + Grad-CAM
│   ├── video/                       # MobileNetV2 + LSTM
│   ├── audio/                       # MFCC + MLP
│   └── fusion/                      # Weighted ensemble + calibration
├── frontend/
│   └── streamlit_app.py             # Dashboard with gauges + charts
├── tests/                           # 49 tests
├── docs/
│   ├── IEEE_Report.md               # Full research paper
│   ├── Presentation.md              # 15-slide deck
│   ├── Poster.md                    # Conference poster
│   └── ADVANCED_IMPLEMENTATION.md   # Implementation guide
├── Dockerfile
├── docker-compose.yml
└── BUILD_GUIDE.md
```

---

## Feature Flags

All advanced modules can be toggled via environment variables:

| Flag | Default | Controls |
|------|---------|----------|
| `TL_INVESTIGATION_MODE` | true | Investigation creation |
| `TL_EVIDENCE_ENGINE` | true | Evidence collection |
| `TL_CONTRADICTION` | true | Cross-modal analysis |
| `TL_EXPLANATION` | true | Human-readable explanations |
| `TL_CASE_MGMT` | true | Case management |
| `TL_HUMAN_REVIEW` | true | Human review queue |
| `TL_SCREENSHOT` | true | Screenshot investigation |
| `TL_CLAIMS` | true | Claim extraction |
| `TL_OCR` | true | OCR endpoint |
| `TL_EXIF` | true | EXIF analysis |
| `TL_CREDIBILITY` | true | Credibility scoring |
| `TL_PERF_MONITOR` | true | Performance tracking |

---

## Training Details

| Model | Architecture | Dataset | Epochs | Accuracy | Training Time |
|-------|-------------|---------|--------|----------|---------------|
| **NLP** | DistilBERT (66M) | 2K synthetic LIAR-style | 1 | 100% val | ~2 min CPU |
| **Image** | EfficientNet-B4 (19M) | 2K synthetic faces | 1 | 66% train | ~5 min CPU |
| **Video** | MobileNetV2 + LSTM | 200 synthetic clips | 3 | 100% val | ~3 min CPU |
| **Audio** | MFCC + MLP (40→128→2) | 600 synthetic audio | 5 | 100% val | ~5 sec CPU |

All models use synthetic data for proof-of-concept. Replace with real datasets (LIAR, FaceForensics++, Celeb-DF, ASVspoof) for production accuracy.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./truthlens.db` | Database connection string |
| `MODEL_DIR` | `./models` | Base directory for model weights |
| `HUGGINGFACE_TOKEN` | — | HF token for gated models (optional) |
| `SECRET_KEY` | `changeme` | Secret key for session signing |
| `TL_*` | `true` | Feature flags (see table above) |

---

## Project Status

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| 0 | Setup | ✅ Complete | — |
| 1 | NLP Model | ✅ Complete | 5/5 |
| 2 | Image Model | ✅ Complete | 5/5 |
| 3 | Video Model | ✅ Complete | 2/2 |
| 4 | Audio Model | ✅ Complete | 3/3 |
| 5 | Fusion + API | ✅ Complete | 6/6 |
| 6 | Frontend | ✅ Complete | — |
| 7 | Reports + XAI | ✅ Complete | — |
| 8 | Stretch Features | ✅ Complete | — |
| 9 | Hardening + Deploy | ✅ Complete | 3/3 |
| 10 | Documentation | ✅ Complete | — |
| **Adv-A** | Core Product Layer | ✅ Complete | 3/3 |
| **Adv-B** | Advanced Intelligence | ✅ Complete | 2/2 |
| **Adv-C** | Case Management | ✅ Complete | 4/4 |
| **Adv-D** | Real-World Features | ✅ Complete | 2/2 |
| **Adv-E** | Performance Monitoring | ✅ Complete | 1/1 |
| **Adv-F** | Feature Flags | ✅ Complete | 1/1 |
| **Total** | | **16/16 phases** | **49 passed** |

---

## Documentation

| Document | Location |
|----------|----------|
| IEEE Report | `docs/IEEE_Report.md` |
| Presentation | `docs/Presentation.md` |
| Poster Concept | `docs/Poster.md` |
| Build Guide | `BUILD_GUIDE.md` |
| Advanced Implementation | `docs/ADVANCED_IMPLEMENTATION.md` |

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

MIT — for educational purposes.

---

Built with [HuggingFace Transformers](https://huggingface.co/docs/transformers/), [PyTorch](https://pytorch.org/), [FastAPI](https://fastapi.tiangolo.com/), [SHAP](https://shap.readthedocs.io/), [timm](https://github.com/huggingface/pytorch-image-models), [Streamlit](https://streamlit.io/), and [ReportLab](https://www.reportlab.com/).
