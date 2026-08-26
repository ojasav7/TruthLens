<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TruthLens — Project Presentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }
        .slide { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 60px; text-align: center; }
        .slide:nth-child(even) { background: #1e293b; }
        h1 { font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        h2 { font-size: 2.2rem; font-weight: 600; margin-bottom: 30px; color: #94a3b8; }
        h3 { font-size: 1.5rem; color: #60a5fa; margin-bottom: 15px; }
        p { font-size: 1.2rem; line-height: 1.8; max-width: 800px; color: #cbd5e1; }
        .subtitle { font-size: 1.3rem; color: #94a3b8; margin-top: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; max-width: 1100px; margin-top: 40px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 30px; text-align: left; }
        .card h3 { margin-bottom: 12px; }
        .card p { font-size: 1rem; }
        .stat { font-size: 3rem; font-weight: 700; color: #60a5fa; }
        .badge { display: inline-block; padding: 6px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; margin: 4px; }
        .badge-green { background: #065f46; color: #6ee7b7; }
        .badge-blue { background: #1e3a5f; color: #93c5fd; }
        .badge-purple { background: #3b0764; color: #c4b5fd; }
        .badge-amber { background: #78350f; color: #fcd34d; }
        table { border-collapse: collapse; margin: 20px auto; }
        th, td { padding: 12px 20px; text-align: left; border-bottom: 1px solid #334155; }
        th { color: #60a5fa; font-weight: 600; }
        .emoji { font-size: 2rem; }
        .flow { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; justify-content: center; margin-top: 30px; }
        .flow-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 15px 25px; font-size: 1rem; }
        .flow-arrow { font-size: 1.5rem; color: #60a5fa; }
    </style>
</head>
<body>

<!-- Slide 1: Title -->
<div class="slide">
    <h1>TruthLens</h1>
    <p class="subtitle">AI-Powered Multimodal Misinformation & Threat Detection Platform</p>
    <p style="margin-top: 40px; color: #64748b;">[Team Names] — [College Name] — August 2026</p>
</div>

<!-- Slide 2: Problem -->
<div class="slide">
    <h2>The Problem</h2>
    <p>Misinformation spreads 6x faster than truth on social media.</p>
    <p style="margin-top: 20px;">Deepfakes, fake news, voice clones, and manipulated videos threaten public trust — and existing tools address only one modality at a time.</p>
    <div class="grid" style="margin-top: 50px;">
        <div class="card">
            <div class="emoji">📰</div>
            <h3>Text</h3>
            <p>Fake news articles, clickbait headlines, manipulated quotes</p>
        </div>
        <div class="card">
            <div class="emoji">🖼️</div>
            <h3>Image</h3>
            <p>Deepfake face swaps, GAN-generated faces, photoshopped content</p>
        </div>
        <div class="card">
            <div class="emoji">🎬</div>
            <h3>Video</h3>
            <p>Face-swap videos, lip-sync manipulation, temporal artifacts</p>
        </div>
        <div class="card">
            <div class="emoji">🔊</div>
            <h3>Audio</h3>
            <p>Voice cloning, synthetic speech, audio manipulation</p>
        </div>
    </div>
</div>

<!-- Slide 3: Solution -->
<div class="slide">
    <h2>Our Solution</h2>
    <p>TruthLens analyzes content across all 4 modalities simultaneously and fuses the results into a single threat score.</p>
    <div class="flow">
        <div class="flow-box">📝 Text</div>
        <div class="flow-box">🖼️ Image</div>
        <div class="flow-box">🎬 Video</div>
        <div class="flow-box">🔊 Audio</div>
        <div class="flow-arrow">→</div>
        <div class="flow-box" style="border-color: #60a5fa;">⚖️ Fusion Layer</div>
        <div class="flow-arrow">→</div>
        <div class="flow-box" style="border-color: #f59e0b;">🎯 Threat Score</div>
    </div>
</div>

<!-- Slide 4: Architecture -->
<div class="slide">
    <h2>System Architecture</h2>
    <table>
        <tr><th>Layer</th><th>Technology</th><th>Purpose</th></tr>
        <tr><td>NLP</td><td>DistilBERT + SHAP</td><td>Fake news classification with token explanations</td></tr>
        <tr><td>Image</td><td>EfficientNet-B4 + Grad-CAM</td><td>Deepfake detection with heatmap explanations</td></tr>
        <tr><td>Video</td><td>MobileNetV2 + LSTM</td><td>Temporal deepfake detection with frame importance</td></tr>
        <tr><td>Audio</td><td>MFCC + MLP</td><td>Voice clone detection with frequency analysis</td></tr>
        <tr><td>Fusion</td><td>Weighted Ensemble</td><td>Dynamic weight renormalization + consistency check</td></tr>
        <tr><td>Backend</td><td>FastAPI + SQLite</td><td>REST API with 29 endpoints</td></tr>
        <tr><td>Frontend</td><td>Streamlit + Plotly</td><td>Interactive dashboard with gauges and charts</td></tr>
    </table>
</div>

<!-- Slide 5: Models -->
<div class="slide">
    <h2>ML Models</h2>
    <div class="grid">
        <div class="card">
            <h3>📝 NLP — DistilBERT</h3>
            <p>66M parameters. Fine-tuned for binary fake/real classification. SHAP explains which words drive the prediction.</p>
            <span class="badge badge-green">100% accuracy</span>
        </div>
        <div class="card">
            <h3>🖼️ Image — EfficientNet-B4</h3>
            <p>19M parameters. Transfer learning from ImageNet. Grad-CAM heatmap shows manipulated regions.</p>
            <span class="badge badge-blue">66% accuracy</span>
        </div>
        <div class="card">
            <h3>🎬 Video — MobileNetV2 + LSTM</h3>
            <p>CNN extracts per-frame features, LSTM captures temporal patterns. Gradient-based frame importance.</p>
            <span class="badge badge-purple">100% accuracy</span>
        </div>
        <div class="card">
            <h3>🔊 Audio — MFCC + MLP</h3>
            <p>40 MFCC coefficients → 2-layer MLP. 50x faster than Wav2Vec2 on CPU.</p>
            <span class="badge badge-amber">100% accuracy</span>
        </div>
    </div>
</div>

<!-- Slide 6: Fusion -->
<div class="slide">
    <h2>Fusion Layer</h2>
    <p>Dynamic weighted ensemble with three key mechanisms:</p>
    <div class="grid" style="margin-top: 40px;">
        <div class="card">
            <h3>⚖️ Weight Renormalization</h3>
            <p>When modalities are missing, weights automatically renormalize to sum to 1.0 over active modalities only.</p>
        </div>
        <div class="card">
            <h3>🔍 Consistency Check</h3>
            <p>Detects when modalities disagree (e.g., text=fake, image=real) and adds a disagreement boost.</p>
        </div>
        <div class="card">
            <h3>📊 Confidence Calibration</h3>
            <p>Platt-style calibration shrinks extreme confidences toward 50% for more reliable scores.</p>
        </div>
    </div>
    <div style="margin-top: 40px;">
        <span class="badge badge-green">Low (0-30)</span>
        <span class="badge badge-amber">Review Needed (31-70)</span>
        <span class="badge" style="background: #7f1d1d; color: #fca5a5;">High Risk (71-100)</span>
    </div>
</div>

<!-- Slide 7: Explainability -->
<div class="slide">
    <h2>Explainability</h2>
    <p>Every prediction includes interpretable explanations.</p>
    <div class="grid" style="margin-top: 40px;">
        <div class="card">
            <h3>📝 SHAP Token Attributions</h3>
            <p>Shows which words in the text drove the classification. "SHOCKING" (+0.05), "fabricating" (+0.04).</p>
        </div>
        <div class="card">
            <h3>🖼️ Grad-CAM Heatmap</h3>
            <p>Visual heatmap overlaid on the image showing which regions the model focused on.</p>
        </div>
        <div class="card">
            <h3>🎬 Frame Importance</h3>
            <p>Gradient-based scoring identifies which video frames contributed most to the prediction.</p>
        </div>
        <div class="card">
            <h3>🔊 Frequency Bands</h3>
            <p>MFCC coefficient importance reveals which frequency bands indicate synthetic speech.</p>
        </div>
    </div>
</div>

<!-- Slide 8: Investigation Engine -->
<div class="slide">
    <h2>Investigation Engine</h2>
    <p>Beyond simple predictions — structured investigations with evidence tracking.</p>
    <div class="grid" style="margin-top: 40px;">
        <div class="card">
            <h3>📋 Evidence Ledger</h3>
            <p>Each modality's output becomes a structured evidence record with type, score, impact, and category.</p>
        </div>
        <div class="card">
            <h3>🔀 Contradiction Detection</h3>
            <p>Cross-modal analysis detects when modalities disagree (text=fake, image=real) and flags conflicts.</p>
        </div>
        <div class="card">
            <h3>💬 Human Explanations</h3>
            <p>Technical signals translated into understandable reasons — never says "definitely fake".</p>
        </div>
        <div class="card">
            <h3>📊 Evidence Metrics</h3>
            <p>Evidence Strength (avg confidence) and Evidence Agreement (consistency across sources).</p>
        </div>
    </div>
</div>

<!-- Slide 9: Case Management -->
<div class="slide">
    <h2>Case Management & Human Review</h2>
    <div class="grid">
        <div class="card">
            <h3>📁 Investigation Cases</h3>
            <p>Group multiple analyses into cases with status tracking: OPEN → UNDER_REVIEW → RESOLVED.</p>
        </div>
        <div class="card">
            <h3>👥 Human Review Queue</h3>
            <p>Reviewers submit verdicts (AUTHENTIC, MANIPULATED, MISLEADING) that never overwrite model predictions.</p>
        </div>
        <div class="card">
            <h3>📜 Audit Trail</h3>
            <p>Every event logged chronologically: case creation, evidence added, review submitted.</p>
        </div>
        <div class="card">
            <h3>🔄 Re-analysis</h3>
            <p>Update investigations when new evidence becomes available — versioned, non-destructive.</p>
        </div>
    </div>
</div>

<!-- Slide 10: Stretch Features -->
<div class="slide">
    <h2>Stretch Features</h2>
    <div class="grid">
        <div class="card">
            <h3>🔍 OCR Extraction</h3>
            <p>Extract text from screenshot images (WhatsApp forwards, social media posts) using pytesseract.</p>
        </div>
        <div class="card">
            <h3>📋 EXIF Metadata</h3>
            <p>Analyze image metadata for editing software, missing camera info, and stripped EXIF data.</p>
        </div>
        <div class="card">
            <h3>🌐 Source Credibility</h3>
            <p>Check URLs against known low-credibility domain lists with heuristic analysis.</p>
        </div>
        <div class="card">
            <h3>🖼️ Screenshot Investigation</h3>
            <p>OCR → extract claims → feed into existing NLP pipeline. No duplicate models.</p>
        </div>
    </div>
</div>

<!-- Slide 11: Demo -->
<div class="slide">
    <h2>Live Demo</h2>
    <p>Walk through the Streamlit dashboard:</p>
    <div class="grid" style="margin-top: 40px;">
        <div class="card">
            <h3>1. Upload Content</h3>
            <p>Text, image, video, or audio — any combination</p>
        </div>
        <div class="card">
            <h3>2. Analyze</h3>
            <p>Click Analyze → see threat score, verdict, breakdown</p>
        </div>
        <div class="card">
            <h3>3. Explain</h3>
            <p>Click Explain buttons for SHAP, Grad-CAM, temporal, frequency</p>
        </div>
        <div class="card">
            <h3>4. Download Report</h3>
            <p>PDF with full analysis, visualizations, and disclaimer</p>
        </div>
    </div>
</div>

<!-- Slide 12: Results -->
<div class="slide">
    <h2>Results</h2>
    <div class="grid">
        <div class="card" style="text-align: center;">
            <div class="stat">29</div>
            <p>API Endpoints</p>
        </div>
        <div class="card" style="text-align: center;">
            <div class="stat">4</div>
            <p>ML Models</p>
        </div>
        <div class="card" style="text-align: center;">
            <div class="stat">49</div>
            <p>Tests Passing</p>
        </div>
        <div class="card" style="text-align: center;">
            <div class="stat">16</div>
            <p>Phases Complete</p>
        </div>
    </div>
    <p style="margin-top: 40px;">All models trained on CPU in under 15 minutes total. Investigation engine adds zero overhead to existing endpoints.</p>
</div>

<!-- Slide 11: Limitations & Future -->
<div class="slide">
    <h2>Limitations & Future Work</h2>
    <div class="grid">
        <div class="card">
            <h3>⚠️ Limitations</h3>
            <p>• Trained on synthetic data<br>• Binary labels only<br>• Static credibility list<br>• No active learning yet</p>
        </div>
        <div class="card">
            <h3>🚀 Future Work</h3>
            <p>• Real-world datasets (LIAR, FaceForensics++)<br>• Active learning loop<br>• Multilingual support<br>• C2PA provenance checking<br>• Browser extension</p>
        </div>
    </div>
</div>

<!-- Slide 12: Thank You -->
<div class="slide">
    <h1>Thank You</h1>
    <p class="subtitle">Questions?</p>
    <p style="margin-top: 40px;">
        <span class="badge badge-blue">github.com/ojasav7/TruthLens</span>
    </p>
    <p style="margin-top: 20px; color: #64748b;">
        Built with HuggingFace Transformers, PyTorch, FastAPI, SHAP, and Streamlit
    </p>
</div>

</body>
</html>
