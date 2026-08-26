# TruthLens

**AI Multimodal Misinformation & Threat Detection Platform**

TruthLens scores text, images, videos, and audio for authenticity and misinformation risk, then explains why — combining NLP, computer vision, and audio analysis with a weighted fusion layer into a single threat score.

[![Tests](https://github.com/ojasav7/TruthLens/actions/workflows/ci.yml/badge.svg)](https://github.com/ojasav7/TruthLens/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Architecture

```
                          ┌─────────────────────┐
                          │   Streamlit Dashboard │  :8501
                          │   (frontend/)         │
                          └─────────┬───────────┘
                                    │ HTTP
                          ┌─────────▼───────────┐
                          │    FastAPI Backend    │  :8000
                          │    (backend/)         │
                          └─────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
    │  /predict/text   │  │ /predict/image  │  │ /predict/video  │
    │  DistilBERT      │  │ EfficientNet-B4 │  │ MobileNetV2+LSTM│
    │  + SHAP explain  │  │ + Grad-CAM      │  │ + frame import. │
    └──────────────────┘  └─────────────────┘  └─────────────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                          ┌─────────▼───────────┐
                          │   Fusion Layer       │
                          │   models/fusion/     │
                          │   Weighted ensemble  │
                          │   Threat scoring     │
                          └─────────┬───────────┘
                                    │
                          ┌─────────▼───────────┐
                          │  /analyze (unified)  │
                          │  + SQLite history    │
                          │  + PDF reports       │
                          └─────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy (async), SQLite |
| **NLP** | DistilBERT (HuggingFace Transformers), SHAP explainability |
| **Image** | EfficientNet-B4 (timm), Grad-CAM heatmaps |
| **Video** | MobileNetV2 + LSTM, OpenCV frame extraction |
| **Audio** | MFCC features + MLP (torchaudio), frequency-band explanations |
| **Fusion** | Weighted ensemble with dynamic renormalization |
| **Frontend** | Streamlit dashboard |
| **Infra** | Docker Compose, pytest |

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
# NLP (DistilBERT — ~2 min on CPU)
python -m models.nlp.train_fast

# Image (EfficientNet-B4 — ~5 min on CPU)
python -m models.image.train

# Video (MobileNetV2+LSTM — ~3 min on CPU)
python -m models.video.train

# Audio (MFCC+MLP — ~5 sec on CPU)
python -m models.audio.train
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
pytest tests/ -v
```

### Docker (alternative)

```bash
docker-compose up --build
```

---

## API Reference

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |

### Per-Modality Predictions

#### `POST /predict/text`

Classify text as real or fake news.

```bash
curl -X POST http://localhost:8000/predict/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Breaking: scientists discover new species"}'
```

**Response:**
```json
{"label": "real", "confidence": 0.87}
```

#### `POST /predict/text/explain`

Classify text with SHAP token attributions.

```bash
curl -X POST http://localhost:8000/predict/text/explain \
  -H "Content-Type: application/json" \
  -d '{"text": "SHOCKING: Government caught fabricating data!", "top_k": 5}'
```

**Response:**
```json
{
  "label": "fake",
  "confidence": 0.92,
  "explained_output": "logits",
  "tokens": [
    {"token": "fabric", "attribution": 0.015},
    {"token": "SHOCKING", "attribution": 0.012}
  ],
  "base_value": 0.0
}
```

#### `POST /predict/image`

Classify image as real or deepfake.

```bash
curl -X POST http://localhost:8000/predict/image \
  -F "file=@photo.jpg"
```

**Response:**
```json
{"label": "real", "confidence": 0.74}
```

#### `POST /predict/image/explain`

Classify image with Grad-CAM heatmap.

```bash
curl -X POST http://localhost:8000/predict/image/explain \
  -F "file=@photo.jpg"
```

**Response:**
```json
{
  "label": "real",
  "confidence": 0.74,
  "heatmap_b64": "<base64-encoded PNG>"
}
```

#### `POST /predict/video`

Classify video with per-frame scores.

```bash
curl -X POST http://localhost:8000/predict/video \
  -F "file=@clip.mp4"
```

**Response:**
```json
{
  "label": "fake",
  "confidence": 0.66,
  "per_frame_scores": [0.7, 0.6, 0.65, ...]
}
```

#### `POST /predict/video/explain`

Classify video with frame importance scores.

```bash
curl -X POST http://localhost:8000/predict/video/explain \
  -F "file=@clip.mp4"
```

**Response:**
```json
{
  "label": "fake",
  "confidence": 0.66,
  "frame_importance": [
    {"frame": 0, "importance": 1.0},
    {"frame": 3, "importance": 0.82}
  ]
}
```

#### `POST /predict/audio`

Classify audio as real or voice clone.

```bash
curl -X POST http://localhost:8000/predict/audio \
  -F "file=@recording.wav"
```

**Response:**
```json
{"label": "cloned", "confidence": 0.91}
```

#### `POST /predict/audio/explain`

Classify audio with frequency-band attributions.

```bash
curl -X POST http://localhost:8000/predict/audio/explain \
  -F "file=@recording.wav"
```

**Response:**
```json
{
  "label": "cloned",
  "confidence": 0.91,
  "explained_output": "logit",
  "top_coefficients": [
    {"mfcc_index": 0, "estimated_freq_hz": 125, "importance": 0.052}
  ],
  "base_value": 0.0
}
```

### Unified Analysis

#### `POST /analyze`

Multimodal analysis — accepts any combination of text, image, video, audio.

```bash
curl -X POST http://localhost:8000/analyze \
  -F "text=Breaking news today" \
  -F "image=@photo.jpg"
```

**Response:**
```json
{
  "id": "a1b2c3d4-...",
  "timestamp": "2026-08-26T12:00:00+00:00",
  "threat_score": 42.5,
  "verdict": "Review Needed",
  "breakdown": {
    "text": {"label": "real", "confidence": 0.87, "weight": 0.25, "threat_contribution": 13.0},
    "image": {"label": "fake", "confidence": 0.65, "weight": 0.75, "threat_contribution": 48.75}
  }
}
```

#### `GET /analyses?limit=20`

List recent analyses.

#### `GET /analyze/{id}/report`

Download a PDF report for a completed analysis.

### Threat Scoring

| Score | Verdict | Meaning |
|-------|---------|---------|
| 0–30 | **Low** | Content appears authentic |
| 31–70 | **Review Needed** | Mixed signals, human review recommended |
| 71–100 | **High Risk** | Strong indicators of manipulation |

Fusion weights: text (25%), image (25%), video (35%), audio (15%). Weights renormalize when not all modalities are present.

---

## Project Structure

```
TruthLens/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── requirements.txt        # Python dependencies
│   ├── db/
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   └── models.py           # Analysis ORM model
│   ├── routers/
│   │   ├── text.py             # POST /predict/text[/explain]
│   │   ├── image.py            # POST /predict/image[/explain]
│   │   ├── video.py            # POST /predict/video[/explain]
│   │   ├── audio.py            # POST /predict/audio[/explain]
│   │   └── analyze.py          # POST /analyze, GET /analyses
│   └── services/
│       ├── model_loader.py     # Singleton model loading
│       └── report_service.py   # PDF generation (ReportLab)
├── models/
│   ├── nlp/
│   │   ├── model.py            # DistilBERT + SHAP explain
│   │   ├── train_fast.py       # CPU training script
│   │   └── weights/            # Trained weights (gitignored)
│   ├── image/
│   │   ├── model.py            # EfficientNet-B4 + Grad-CAM
│   │   ├── train.py
│   │   └── weights/
│   ├── video/
│   │   ├── model.py            # MobileNetV2 + LSTM + temporal
│   │   ├── train.py
│   │   └── weights/
│   ├── audio/
│   │   ├── model.py            # MFCC + MLP + freq-band explain
│   │   ├── train.py
│   │   └── weights/
│   └── fusion/
│       └── fuse.py             # Weighted ensemble fusion
├── frontend/
│   └── streamlit_app.py        # Streamlit dashboard
├── tests/
│   ├── conftest.py             # Model pre-loading for tests
│   ├── test_nlp.py             # 5 tests
│   ├── test_image.py           # 5 tests
│   ├── test_video.py           # 2 tests
│   ├── test_audio.py           # 3 tests
│   └── test_api.py             # 15 integration tests
├── data/
│   └── scripts/                # Dataset generators
├── notebooks/                  # Training notebooks (Colab)
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Training Details

| Model | Architecture | Dataset | Epochs | Accuracy | Training Time |
|-------|-------------|---------|--------|----------|---------------|
| **NLP** | DistilBERT (66M params) | 2K synthetic LIAR-style | 1 | 100% val | ~2 min CPU |
| **Image** | EfficientNet-B4 (19M params) | 2K synthetic faces | 1 | 66% train | ~5 min CPU |
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

## Acknowledgments

## Project Status

| Phase | Name | Status |
|-------|------|--------|
| 0 | Setup | ✅ Complete |
| 1 | NLP Model | ✅ Complete |
| 2 | Image Model | ✅ Complete |
| 3 | Video Model | ✅ Complete |
| 4 | Audio Model | ✅ Complete |
| 5 | Fusion + API | ✅ Complete |
| 6 | Frontend | ✅ Complete |
| 7 | Reports + XAI | ✅ Complete |
| 8 | Stretch Features | ✅ Complete |
| 9 | Hardening + Deploy | ✅ Complete |
| 10 | Documentation | ✅ Complete |

### Stretch Features

| Feature | Endpoint | Description |
|---------|----------|-------------|
| OCR | `POST /stretch/ocr` | Extract text from images |
| EXIF | `POST /stretch/exif` | Analyze image metadata |
| Credibility | `POST /stretch/credibility` | Score URL credibility |

---

## Documentation

| Document | Location |
|----------|----------|
| IEEE Report | `docs/IEEE_Report.md` |
| Presentation | `docs/Presentation.md` (HTML) |
| Poster Concept | `docs/Poster.md` |
| Build Guide | `BUILD_GUIDE.md` |

---

Built with [HuggingFace Transformers](https://huggingface.co/docs/transformers/), [PyTorch](https://pytorch.org/), [FastAPI](https://fastapi.tiangolo.com/), [SHAP](https://shap.readthedocs.io/), [timm](https://github.com/huggingface/pytorch-image-models), and [Streamlit](https://streamlit.io/).
