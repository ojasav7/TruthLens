# AI Multimodal Misinformation & Threat Detection Platform
### Master Build Guide — Phase-by-Phase (Human + AI Coding Agent Ready)

> **How to use this file:** This is the single source of truth for building the project from an empty folder to a finished, demo-ready prototype. It is written so a human developer can follow it step-by-step, AND so an AI coding agent (Claude Code, Cursor, Copilot Workspace, etc.) can be pointed at this file and told "build Phase 1" / "build Phase 2" etc. and know exactly what to produce, in what folder, with what interface.
>
> Rule for every phase: **do not start the next phase until the current phase runs and produces the expected output.** Each phase has a "Definition of Done" checklist — treat it as a hard gate.

---

## 0. Project Identity

| | |
|---|---|
| **Name** | TruthLens (working name — rename freely) |
| **One-liner** | A platform that scores text, images, videos, and audio for authenticity/misinformation risk, and explains why. |
| **Team size** | 4 members |
| **Core modules** | NLP (fake news), CV (image deepfake), Video (temporal deepfake), Audio (voice clone), Fusion, Dashboard |
| **Stretch modules** | C2PA provenance check, claim-matching, XAI, OCR/screenshot, bots, browser extension |

---

## 1. Repository Structure (create this exact skeleton first)

```
truthlens/
├── README.md
├── BUILD_GUIDE.md                 ← this file
├── .env.example
├── .gitignore
├── docker-compose.yml             ← Phase 6
├── data/
│   ├── raw/                       ← downloaded datasets (gitignored)
│   ├── processed/                 ← preprocessed tensors/csv (gitignored)
│   └── scripts/                   ← download + preprocessing scripts
├── models/
│   ├── nlp/                       ← Member 1
│   │   ├── train.py
│   │   ├── infer.py
│   │   ├── model.py
│   │   └── weights/               ← gitignored, or Git LFS
│   ├── image/                     ← Member 2
│   │   ├── train.py
│   │   ├── infer.py
│   │   ├── model.py
│   │   └── weights/
│   ├── video/                     ← Member 3
│   │   ├── train.py
│   │   ├── infer.py
│   │   ├── model.py
│   │   └── weights/
│   ├── audio/                     ← Member 3
│   │   ├── train.py
│   │   ├── infer.py
│   │   ├── model.py
│   │   └── weights/
│   └── fusion/                    ← Member 4
│       └── fuse.py
├── backend/
│   ├── main.py                    ← FastAPI app entrypoint
│   ├── routers/
│   │   ├── text.py
│   │   ├── image.py
│   │   ├── video.py
│   │   ├── audio.py
│   │   └── analyze.py             ← the combined /analyze endpoint
│   ├── services/
│   │   ├── model_loader.py
│   │   ├── fusion_service.py
│   │   └── report_service.py      ← PDF generation
│   ├── db/
│   │   ├── models.py               (SQLAlchemy)
│   │   └── database.py
│   └── requirements.txt
├── frontend/
│   └── streamlit_app.py           ← Phase 5 (swap for React later if wanted)
├── tests/
│   ├── test_nlp.py
│   ├── test_image.py
│   ├── test_video.py
│   ├── test_audio.py
│   └── test_api.py
└── notebooks/
    ├── 01_nlp_training.ipynb      ← Colab/Kaggle training notebooks live here
    ├── 02_image_training.ipynb
    ├── 03_video_training.ipynb
    └── 04_audio_training.ipynb
```

**Action for AI agent:** Create this full folder/file skeleton with placeholder files (empty functions, TODO comments) before writing any real logic. Commit as "chore: scaffold repo structure".

---

## 2. Phase Roadmap (Overview)

| Phase | Name | Owner(s) | Output |
|---|---|---|---|
| 0 | Setup | Everyone | Repo, env, GitHub, datasets downloaded |
| 1 | NLP Model | Member 1 | Fake news classifier + `/predict/text` |
| 2 | Image Model | Member 2 | Deepfake image classifier + `/predict/image` |
| 3 | Video Model | Member 3 | Deepfake video classifier + `/predict/video` |
| 4 | Audio Model | Member 3 | Voice clone classifier + `/predict/audio` |
| 5 | Fusion + Backend API | Member 4 | Unified `/analyze` endpoint |
| 6 | Frontend Dashboard | Member 4 (+ all) | Streamlit UI, live demo-able |
| 7 | Reports + Explainability | All | PDF report, SHAP/Grad-CAM |
| 8 | Stretch Features | All (pick 2–3) | See Section 10 |
| 9 | Hardening + Deployment | All | Hosted demo link |
| 10 | Documentation + Submission | All | Report, PPT, video, poster |

Each member can start their Phase (1/2/3-4) in **parallel** right after Phase 0 — they don't depend on each other until Phase 5.

---

## 3. Phase 0 — Setup (Week 1)

### Human tasks
1. Create a **private GitHub repo** named `truthlens`. Add all 4 members as collaborators.
2. Each member creates a **Google Colab** and **Kaggle** account (for free GPU).
3. Install locally: Python 3.10+, Node.js (for frontend later), Git, Docker (optional but recommended).
4. Create `.env` file locally (never commit it) from `.env.example`:
   ```
   DATABASE_URL=sqlite:///./truthlens.db
   MODEL_DIR=./models
   HUGGINGFACE_TOKEN=
   SECRET_KEY=changeme
   ```
5. Download datasets (run once, store paths, don't commit raw data):

| Dataset | Command / Source |
|---|---|
| LIAR | `kaggle datasets download -d doanquanvietnamca/liar-dataset` (or from UCI) |
| FakeNewsNet | `git clone https://github.com/KaiDMML/FakeNewsNet` |
| FaceForensics++ | Request access at https://github.com/ondyari/FaceForensics — academic email required |
| DFDC sample | `kaggle competitions download -c deepfake-detection-challenge` (use the small sample set, ~4GB, not the full 470GB) |
| Celeb-DF | https://github.com/yuezunli/celeb-deepfakeforensics (request form) |
| ASVspoof 2019 | https://datashare.ed.ac.uk/handle/10283/3336 |

> **Tip:** For a prototype, you do NOT need full datasets. Use 5,000–20,000 samples per model — enough to train and demonstrate real accuracy without needing days of GPU time.

### Definition of Done (Phase 0)
- [ ] Repo exists, all 4 members can push
- [ ] Folder skeleton from Section 1 is committed
- [ ] Each member has downloaded their dataset subset and can load it in a notebook
- [ ] `.env.example` exists, `.env` is gitignored

---

## 4. Phase 1 — NLP Fake News Model (Member 1)

**Goal:** A model that takes text and returns `{label: "fake"|"real", confidence: 0.0-1.0}`.

### Steps
1. In `notebooks/01_nlp_training.ipynb` (Colab):
   - Load LIAR + FakeNewsNet, merge/clean into a single `(text, label)` CSV
   - Tokenize with `bert-base-uncased` tokenizer (HuggingFace)
   - Fine-tune `BertForSequenceClassification` (2 labels) — 3-5 epochs, batch size 16
   - Evaluate: accuracy, F1, confusion matrix
   - Target: **>85% accuracy**
   - Save weights: `model.save_pretrained('nlp_model')`, zip, download
2. Move weights into `models/nlp/weights/`
3. Write `models/nlp/model.py`:
   ```python
   class FakeNewsClassifier:
       def __init__(self, weights_path): ...
       def predict(self, text: str) -> dict:
           # returns {"label": "fake"/"real", "confidence": float}
   ```
4. Write `models/nlp/infer.py` — CLI script to test: `python infer.py --text "..."`
5. Wire into `backend/routers/text.py` as `POST /predict/text`

### Definition of Done (Phase 1)
- [ ] Notebook runs end-to-end on Colab GPU
- [ ] Accuracy ≥ 85% logged in notebook output
- [ ] `models/nlp/weights/` populated
- [ ] `POST /predict/text {"text": "..."}` returns valid JSON locally
- [ ] `tests/test_nlp.py` passes with at least 3 sample inputs

---

## 5. Phase 2 — Image Deepfake Model (Member 2)

**Goal:** A model that takes an image and returns `{label: "fake"|"real", confidence: float}`.

### Steps
1. In `notebooks/02_image_training.ipynb`:
   - Extract real + fake frames/images from FaceForensics++
   - Face-crop with MTCNN (`facenet-pytorch`), resize to 224×224, normalize
   - Load `EfficientNet-B4` pretrained on ImageNet (via `timm` library), replace head with 2-class classifier
   - Augment: random flip, brightness/contrast jitter, slight rotation
   - Train 5-10 epochs, target **>90% accuracy / AUC-ROC**
   - Save weights
2. Move weights into `models/image/weights/`
3. Write `models/image/model.py` with same `predict()` contract pattern
4. Wire into `backend/routers/image.py` as `POST /predict/image` (multipart file upload)

### Definition of Done (Phase 2)
- [ ] Notebook runs, AUC-ROC ≥ 0.90 logged
- [ ] `models/image/weights/` populated
- [ ] `POST /predict/image` accepts an uploaded file and returns valid JSON
- [ ] `tests/test_image.py` passes on 3 sample images (1 real, 2 fake or vice versa)

---

## 6. Phase 3 — Video Deepfake Model (Member 3)

**Goal:** A model that takes a video file and returns `{label, confidence, per_frame_scores: [...]}`.

### Steps
1. In `notebooks/03_video_training.ipynb`:
   - Use DFDC sample set (or FaceForensics++ videos)
   - Extract frames at 1fps with OpenCV, face-crop with MTCNN
   - Build sequences of 20 frames per clip
   - Architecture: CNN backbone (reuse EfficientNet from Phase 2, frozen or fine-tuned) → LSTM over frame embeddings → classifier head
   - Train, target **>88% AUC-ROC**
   - Save weights
2. Write `models/video/model.py`:
   ```python
   class VideoDeepfakeDetector:
       def predict(self, video_path: str) -> dict:
           # 1. extract frames, 2. run CNN+LSTM, 3. aggregate
   ```
3. Wire into `backend/routers/video.py` as `POST /predict/video`

### Definition of Done (Phase 3)
- [ ] Notebook runs, AUC-ROC ≥ 0.88 logged
- [ ] `models/video/weights/` populated
- [ ] `POST /predict/video` accepts an uploaded video and returns JSON with per-frame + aggregate score
- [ ] `tests/test_video.py` passes on 1-2 short sample clips

---

## 7. Phase 4 — Audio Voice Clone Model (Member 3)

**Goal:** A model that takes an audio file and returns `{label: "cloned"|"real", confidence}`.

### Steps
1. In `notebooks/04_audio_training.ipynb`:
   - Load ASVspoof 2019 dataset
   - Use pretrained `Wav2Vec2` (facebook/wav2vec2-base) from HuggingFace as feature extractor
   - Add a classification head (2 classes), fine-tune
   - Target **>87% accuracy / low EER**
   - Save weights
2. Write `models/audio/model.py` and `infer.py`
3. Add a utility to extract audio from video (`ffmpeg -i input.mp4 -q:a 0 -map a output.wav`) — used when a video is submitted, so audio gets checked too
4. Wire into `backend/routers/audio.py` as `POST /predict/audio`

### Definition of Done (Phase 4)
- [ ] Notebook runs, EER/accuracy logged and meets target
- [ ] `models/audio/weights/` populated
- [ ] `POST /predict/audio` returns valid JSON
- [ ] Audio auto-extraction from an uploaded video works

---

## 8. Phase 5 — Fusion Layer + Unified Backend (Member 4, needs Phases 1-4 outputs)

**Goal:** One endpoint that accepts any combination of text/image/video/audio and returns one combined verdict.

### Steps
1. `backend/services/model_loader.py` — loads all 4 models once at startup (singleton pattern), not per-request
2. `models/fusion/fuse.py`:
   ```python
   def fuse(scores: dict, weights={"text":0.25,"image":0.25,"video":0.35,"audio":0.15}) -> dict:
       # weighted average of whichever modalities were present (renormalize weights
       # to sum to 1 over only the modalities actually submitted)
       # returns {"threat_score": 0-100, "verdict": "Low"/"Review"/"High Risk", "breakdown": {...}}
   ```
3. `backend/routers/analyze.py` — `POST /analyze` accepts any subset of `{text, image, video, audio}`, calls the relevant sub-predictors, fuses, returns combined result + stores to DB
4. `backend/db/models.py` — SQLAlchemy models: `Analysis(id, timestamp, input_type, scores_json, verdict, threat_score)`
5. Add risk tiers to fusion output:
   - `0-30` → Low
   - `31-70` → Review Needed
   - `71-100` → High Risk
6. Write OpenAPI docs (FastAPI gives this for free at `/docs`) — screenshot it for your report

### API Contract (lock this — frontend depends on it)
```jsonc
// POST /analyze  (multipart/form-data: text?, image?, video?, audio?)
// Response:
{
  "id": "uuid",
  "timestamp": "2026-08-22T10:00:00Z",
  "threat_score": 72,
  "verdict": "Review Needed",
  "breakdown": {
    "text":  {"label": "fake", "confidence": 0.81},
    "image": {"label": "real", "confidence": 0.60},
    "video": null,
    "audio": null
  }
}
```

### Definition of Done (Phase 5)
- [ ] `POST /analyze` works with any single modality and any combination
- [ ] Fusion weights renormalize correctly when modalities are missing
- [ ] Every analysis is saved to the DB
- [ ] `/docs` (Swagger UI) loads and all endpoints are testable from the browser
- [ ] `tests/test_api.py` covers at least: text-only, image-only, text+image, all-four

---

## 9. Phase 6 — Frontend Dashboard (Member 4 + all, for polish)

**Goal:** A usable UI a non-technical evaluator can operate.

### Steps (Streamlit — fastest path to a working demo)
1. `frontend/streamlit_app.py`:
   - File upload widgets (text box, image, video, audio — all optional, at least one required)
   - "Analyze" button → calls `POST /analyze`
   - Show: threat score gauge (color-coded), per-module breakdown bar chart, verdict badge
   - History table: pull last N analyses from `GET /analyses` (add this endpoint)
   - "Download PDF Report" button (Phase 7)
2. Run locally: `streamlit run frontend/streamlit_app.py`

### Optional upgrade path (if time allows)
Swap Streamlit for **React + TailwindCSS**, calling the same FastAPI backend — same API contract, no backend changes needed. Do this only after Streamlit version fully works — never build both from scratch in parallel.

### Definition of Done (Phase 6)
- [ ] A user can upload any combination of inputs and get a result in the browser
- [ ] Threat score and breakdown are visually clear (gauge/chart, not just numbers)
- [ ] History view shows past analyses

---

## 10. Phase 7 — Reports + Explainability (All members, split by module)

| Feature | Who builds it | Library |
|---|---|---|
| PDF report generation | Member 4 | `reportlab` or `weasyprint` |
| SHAP explanation for text | Member 1 | `shap` |
| Grad-CAM heatmap for image | Member 2 | `pytorch-grad-cam` |
| Frame-level highlight for video | Member 3 | reuse Grad-CAM per-frame |

`backend/services/report_service.py`:
- Input: an `Analysis` record → Output: PDF with input preview, per-module score, explanation visual, final verdict, timestamp, disclaimer text
- New endpoint: `GET /analyze/{id}/report` → returns PDF

### Definition of Done (Phase 7)
- [ ] Every completed analysis can generate a downloadable PDF
- [ ] Text predictions show highlighted "suspicious" words/phrases
- [ ] Image/video predictions show a heatmap over the manipulated region

---

## 11. Phase 8 — Stretch Features (Pick 2–3, don't try all)

These are **plug-in modules** — none of them require changing the core architecture, they just add new signals into the fusion layer or new endpoints. Pick based on team bandwidth after Phase 7 is done.

### Tier A — Do these first (low effort, high impact)
- **C2PA provenance check** — `pip install c2pa-python`, check uploaded images/videos for a valid signed manifest before running deep models. If valid → mark "Verified Source" and skip/downweight deepfake score.
- **OCR / Screenshot support** — `pytesseract` extracts text from uploaded screenshot images → feeds into the NLP pipeline. Very common real-world input (WhatsApp forwards).
- **Auto PDF report** — see Phase 7 if not already done.
- **Claim-matching via Google Fact Check Tools API** (free) — before running your own model, check if the exact claim is already fact-checked; show that verdict alongside your model's.

### Tier B — Do these if Tier A is done early
- **Telegram bot** (`python-telegram-bot`) — forward text/image/video to bot, get verdict back. Very demoable, looks like a real product.
- **Metadata/EXIF analysis** — `Pillow` reads EXIF; flag missing/stripped metadata as a weak signal.
- **Source credibility scoring** — static CSV of known low-credibility domains, checked when a URL is submitted.
- **Multilingual NLP (Hindi)** — swap/duplicate the text pipeline with `google/muril-base-cased`, fine-tune on a Hindi fake news dataset.

### Tier C — Only if way ahead of schedule
- Browser extension, mobile app, blockchain audit trail, WhatsApp bot, analytics heat map, topic clustering, adversarial robustness testing, ensemble voting, active learning loop.

> Each stretch feature should be built as a **separate module** with its own `predict()`/`check()` function that plugs into `fuse()` — never hardcode a stretch feature directly into the core pipeline. This keeps the system demoable at every stage even if a stretch feature breaks.

---

## 12. Phase 9 — Hardening + Deployment

1. Add `SlowAPI` rate limiting to the backend (5 lines)
2. Add basic auth if a login system is in scope, otherwise skip
3. Write `Dockerfile` for backend, `docker-compose.yml` to run backend + frontend + DB together
4. Deploy:
   - Backend → **Render** or **Railway** (free tier)
   - Frontend → **Streamlit Community Cloud** (free) or same host as backend
   - Model weights → if too large for git, host on **Hugging Face Hub** and download at container startup
5. Do a full **robustness check**: recompress 10 test videos/images at 3 quality levels, confirm accuracy doesn't collapse — write results into your report's "Limitations" section

### Definition of Done (Phase 9)
- [ ] Live public URL works end-to-end
- [ ] Rate limiting prevents abuse
- [ ] Robustness test results documented

---

## 13. Phase 10 — Documentation + Submission

- [ ] IEEE-format project report (abstract, literature review, methodology, results, limitations, conclusion, ≥15 references)
- [ ] PPT for viva/presentation
- [ ] 3–5 minute demo video showing all modalities live
- [ ] GitHub README with architecture diagram, setup instructions, screenshots
- [ ] Project poster

---

## 14. Instructions for an AI Coding Agent

If you are an AI agent (Claude Code, etc.) executing this file:

1. Always work **one phase at a time**, in the order listed in Section 2.
2. Before writing any model training code, check whether `notebooks/` or `models/*/weights/` already has output for that phase — do not retrain if weights already exist and pass their tests.
3. Every module (`nlp`, `image`, `video`, `audio`) must implement the same interface shape: a `predict()`/`infer()` method returning `{"label": str, "confidence": float}` (video/audio may add extra fields) — this is required for Phase 5 fusion to work without rewrites.
4. Never hardcode file paths — read from `.env` / `MODEL_DIR`.
5. After finishing a phase, run its Definition of Done checklist as actual commands (pytest, curl requests to the running server, etc.) and report pass/fail before moving to the next phase.
6. When adding a Phase 8 stretch feature, create it as an isolated function/module and register it into `fuse()` via a dict entry — do not modify existing module code to add it.
7. Keep `backend/routers/*.py` thin — business logic belongs in `backend/services/` or `models/*/model.py`, not in the route handler.

---

## 15. Quick Reference — All Endpoints

| Method | Path | Purpose | Phase |
|---|---|---|---|
| POST | `/predict/text` | NLP-only fake news check | 1 |
| POST | `/predict/image` | Image-only deepfake check | 2 |
| POST | `/predict/video` | Video-only deepfake check | 3 |
| POST | `/predict/audio` | Audio-only voice clone check | 4 |
| POST | `/analyze` | Combined multimodal analysis | 5 |
| GET | `/analyses` | History list | 6 |
| GET | `/analyze/{id}/report` | Download PDF report | 7 |
| POST | `/analyze/{id}/provenance` | C2PA check (stretch) | 8 |
| POST | `/analyze/{id}/factcheck` | Claim-matching (stretch) | 8 |

---

## 16. Scope for Future Extension (beyond submission)

This architecture is intentionally modular so that after your evaluation, the project can keep growing without a rewrite:

- Swap Streamlit → full React dashboard with auth and roles
- Swap SQLite → PostgreSQL for multi-user production use
- Add ensemble voting (multiple models per modality) once single models are stable
- Add active learning: store user-corrected labels, periodically retrain
- Add real-time/live-call scanning mode (WebRTC streaming into the video/audio pipeline)
- Package as a browser extension or WhatsApp/Telegram bot for real public use
- Publish the fusion methodology as a short paper/preprint if results are strong

**End of Build Guide.**
