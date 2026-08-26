# TruthLens — Project Poster

## Layout (A0 or A1 size, portrait orientation)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     TRUTHLENS                               │
│     AI-Powered Multimodal Misinformation                    │
│            & Threat Detection                               │
│                                                             │
│         [Team Names] — [College Name]                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   PROBLEM    │  │  SOLUTION    │  │ ARCHITECTURE │     │
│  │              │  │              │  │              │     │
│  │ Misinform-   │  │ Analyze 4    │  │ DistilBERT   │     │
│  │ ation spans  │  │ modalities   │  │ EfficientNet │     │
│  │ text, image, │  │ simultaneously│ │ MobileNet+LSTM│    │
│  │ video, audio │  │ with fused   │  │ MFCC+MLP     │     │
│  │              │  │ threat score │  │ Fusion Layer │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SYSTEM ARCHITECTURE                     │   │
│  │                                                     │   │
│  │  Input → [NLP] [Image] [Video] [Audio] → Fusion    │   │
│  │                         ↓                           │   │
│  │                   Threat Score                      │   │
│  │                    (0-100)                          │   │
│  │                         ↓                           │   │
│  │              [Explainability Layer]                  │   │
│  │        SHAP  Grad-CAM  Temporal  Frequency          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  KEY RESULTS                        │   │
│  │                                                     │   │
│  │  NLP: 100% acc  │  Image: 66% acc                  │   │
│  │  Video: 100% acc │  Audio: 100% acc                 │   │
│  │                                                     │   │
│  │  29 API Endpoints │ 49 Tests Passing                │   │
│  │  4 ML Models      │ 16 Phases Complete              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ INVESTIGATION│  │  EXPLAINABILITY│ │   DEPLOY     │     │
│  │              │  │              │  │              │     │
│  │ Evidence     │  │ SHAP tokens  │  │ Docker       │     │
│  │ Ledger       │  │ Grad-CAM     │  │ FastAPI      │     │
│  │ Contradiction│  │ Frame import.│  │ Streamlit    │     │
│  │ Case Mgmt    │  │ Freq bands   │  │ Rate limit   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    TECH STACK                        │   │
│  │  PyTorch • HuggingFace • FastAPI • SHAP • Streamlit │   │
│  │  Docker • SQLAlchemy • ReportLab • Plotly • OpenCV   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  github.com/ojasav7/TruthLens                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark Navy | #0f172a |
| Title | Gradient Blue-Purple | #60a5fa → #a78bfa |
| Cards | Slate | #1e293b |
| Borders | Muted Gray | #334155 |
| Text | Light Gray | #e2e8f0 |
| Accent | Blue | #60a5fa |
| Success | Green | #22c55e |
| Warning | Amber | #f59e0b |
| Danger | Red | #ef4444 |

## Fonts

- **Title:** Inter Bold, 48pt
- **Headers:** Inter SemiBold, 24pt
- **Body:** Inter Regular, 14pt
- **Code:** JetBrains Mono, 12pt

## Creation Notes

To create the actual poster:
1. Use Figma, Canva, or Adobe Illustrator
2. Export as PDF at 300 DPI
3. Print at A0 (841×1189mm) or A1 (594×841mm)
4. Use the color scheme and layout above
