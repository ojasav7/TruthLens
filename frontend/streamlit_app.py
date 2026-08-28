"""
TruthLens Dashboard — Forensic Intelligence Platform
Design System: Stitch Design + Vercel Web Interface Guidelines
Theme: Dark Ops-Center with Cyber/Tech atmosphere
"""

import io
import os
import base64
import time as _time
import requests
import streamlit as st
import plotly.graph_objects as go
from PIL import Image

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TruthLens — Forensic Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DESIGN SYSTEM CSS
# ============================================================
st.markdown("""
<style>
/* === Design System Tokens === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    /* Colors */
    --bg-primary: #0f172a;
    --bg-surface: #1e293b;
    --bg-elevated: #253349;
    --border-default: #334155;
    --border-active: #475569;
    --cyan: #06b6d4;
    --cyan-hover: #0891b2;
    --cyan-glow: rgba(6, 182, 212, 0.15);
    --crimson: #ef4444;
    --amber: #f59e0b;
    --emerald: #22c55e;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-tertiary: #64748b;

    /* Typography */
    --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'Source Code Pro', monospace;

    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 12px;
    --space-lg: 16px;
    --space-xl: 24px;
    --space-2xl: 32px;

    /* Radius */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-pill: 50px;

    /* Shadows */
    --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.3);
    --shadow-elevated: 0 4px 12px rgba(0, 0, 0, 0.4);
    --shadow-glow-cyan: 0 0 20px rgba(6, 182, 212, 0.2);
    --shadow-glow-danger: 0 0 20px rgba(239, 68, 68, 0.3);
}

/* === Base === */
.stApp {
    background-color: var(--bg-primary);
    font-family: var(--font-body);
}
section[data-testid="stSidebar"] {
    background-color: #0c1322;
    border-right: 1px solid var(--border-default);
}
div[data-testid="stVerticalBlock"] > div {
    margin-bottom: var(--space-sm);
}

/* === Focus States (WCAG 2.2 AA) === */
:focus-visible {
    outline: 2px solid var(--cyan) !important;
    outline-offset: 2px !important;
    border-radius: var(--radius-sm);
}
.stButton > button:focus-visible {
    box-shadow: 0 0 0 3px var(--cyan-glow) !important;
}
.stTabs [data-baseweb="tab"]:focus-visible {
    outline: 2px solid var(--cyan) !important;
    outline-offset: -2px !important;
}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    padding: 8px 16px;
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    font-family: var(--font-body);
}
.stTabs [data-baseweb="tab"]:hover {
    border-color: var(--border-active);
    color: var(--text-primary);
    background: var(--bg-elevated);
}
.stTabs [aria-selected="true"] {
    background: var(--cyan-glow) !important;
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
    font-weight: 600;
}

/* === Metric Cards === */
div[data-testid="stMetric"] {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    transition: border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: var(--border-active);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.75rem !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-variant-numeric: tabular-nums;
}

/* === Verdict Badge === */
.verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 28px;
    border-radius: var(--radius-pill);
    font-size: 1.2rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    text-align: center;
    font-family: var(--font-body);
    transition: all 0.3s ease;
}
.verdict-low {
    background: rgba(34, 197, 94, 0.12);
    color: var(--emerald);
    border: 2px solid var(--emerald);
    box-shadow: 0 0 16px rgba(34, 197, 94, 0.15);
}
.verdict-review {
    background: rgba(245, 158, 11, 0.12);
    color: var(--amber);
    border: 2px solid var(--amber);
    box-shadow: 0 0 16px rgba(245, 158, 11, 0.15);
}
.verdict-high {
    background: rgba(239, 68, 68, 0.12);
    color: var(--crimson);
    border: 2px solid var(--crimson);
    box-shadow: var(--shadow-glow-danger);
    animation: pulse-danger 2s ease-in-out infinite;
}

/* === Status Indicator === */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 500;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.status-dot.green {
    background: var(--emerald);
    box-shadow: 0 0 8px var(--emerald);
}
.status-dot.red {
    background: var(--crimson);
    box-shadow: 0 0 8px var(--crimson);
}

/* === Ops Card === */
.ops-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-md);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.ops-card:hover {
    border-color: var(--border-active);
    box-shadow: var(--shadow-card);
}

/* === Progress Bar === */
.progress-track {
    background: rgba(255, 255, 255, 0.06);
    border-radius: 3px;
    height: 6px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* === Button Styles === */
.stButton > button {
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-elevated);
}
.stButton > button:active {
    transform: translateY(0);
}

/* === Input Fields === */
.stTextArea textarea,
.stTextInput input {
    font-family: var(--font-body) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-default) !important;
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    transition: border-color 0.2s ease !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px var(--cyan-glow) !important;
}

/* === Expander === */
.streamlit-expanderHeader {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    font-family: var(--font-body) !important;
    transition: border-color 0.2s ease !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--border-active) !important;
}

/* === Animations === */
@keyframes pulse-danger {
    0%, 100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); }
    50% { box-shadow: 0 0 24px rgba(239, 68, 68, 0.5); }
}
@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.animate-in {
    animation: fade-in-up 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* === Reduced Motion === */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* === Scrollbar === */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-active); }

/* === Typography === */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-body) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-primary) !important;
    text-wrap: balance;
}
.stMarkdown p {
    line-height: 1.6;
}

/* === Progress Bar Override === */
.stProgress > div > div > div > div {
    background: var(--cyan) !important;
    border-radius: 3px !important;
}

/* === Toast Override === */
.stToast {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius-md) !important;
}

/* === File Uploader === */
.stFileUploader {
    border: 2px dashed var(--border-default) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-surface) !important;
    transition: border-color 0.2s ease !important;
}
.stFileUploader:hover {
    border-color: var(--cyan) !important;
}
.stFileUploader label {
    color: var(--text-secondary) !important;
}

/* === Score Display === */
.score-display {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-weight: 700;
}

/* === Chip/Tag === */
.chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid;
}
.chip-cyan {
    background: var(--cyan-glow);
    color: var(--cyan);
    border-color: rgba(6, 182, 212, 0.3);
}
.chip-emerald {
    background: rgba(34, 197, 94, 0.12);
    color: var(--emerald);
    border-color: rgba(34, 197, 94, 0.3);
}
.chip-amber {
    background: rgba(245, 158, 11, 0.12);
    color: var(--amber);
    border-color: rgba(245, 158, 11, 0.3);
}
.chip-crimson {
    background: rgba(239, 68, 68, 0.12);
    color: var(--crimson);
    border-color: rgba(239, 68, 68, 0.3);
}

/* === Divider === */
.divider {
    border: none;
    border-top: 1px solid var(--border-default);
    margin: var(--space-lg) 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER BAR
# ============================================================
@st.cache_data(ttl=300)
def check_backend():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.ok
    except Exception:
        return False

backend_up = check_backend()
status_color = "green" if backend_up else "red"
status_text = "LIVE" if backend_up else "DOWN"

st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid var(--border-default); margin-bottom:var(--space-xl);">
    <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.6rem;">🔍</span>
        <span style="font-size:1.3rem; font-weight:700; color:var(--text-primary); letter-spacing:0.06em; font-family:var(--font-body);">TRUTHLENS</span>
        <span class="chip chip-cyan">v1.0.0</span>
    </div>
    <div style="display:flex; align-items:center; gap:20px;">
        <span class="status-indicator" style="color:{'var(--emerald)' if backend_up else 'var(--crimson)'};">
            <span class="status-dot {status_color}"></span>
            {status_text}
        </span>
        <a href="{API_URL}/docs" target="_blank" rel="noopener noreferrer"
           style="color:var(--cyan); text-decoration:none; font-size:0.85rem; font-weight:500; transition:color 0.2s;"
           onmouseover="this.style.color='var(--cyan-hover)'"
           onmouseout="this.style.color='var(--cyan)'">
           API Docs ↗
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

if not backend_up:
    st.warning("⚠️ Backend not running. Start with: `uvicorn backend.main:app --reload`")


# ============================================================
# SIDEBAR — INPUT PANEL
# ============================================================
with st.sidebar:
    st.markdown("### 📝 Analysis Input")

    input_tabs = st.tabs(["📝 Text", "🖼️ Image", "🎬 Video", "🔊 Audio"])

    text_input = None
    image_file = None
    video_file = None
    audio_file = None

    with input_tabs[0]:
        text_input = st.text_area(
            "Text to analyze",
            placeholder="Paste suspicious news, headline, or social media post…",
            height=150,
            label_visibility="collapsed",
        )
        if text_input:
            char_count = len(text_input)
            st.caption(f"📊 {char_count} characters · {len(text_input.split())} words")

    with input_tabs[1]:
        image_file = st.file_uploader(
            "Upload image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            help="Supports JPEG, PNG, WebP formats",
        )

    with input_tabs[2]:
        video_file = st.file_uploader(
            "Upload video",
            type=["mp4", "avi", "mov", "webm"],
            label_visibility="collapsed",
            help="Supports MP4, AVI, MOV, WebM formats",
        )

    with input_tabs[3]:
        audio_file = st.file_uploader(
            "Upload audio",
            type=["wav", "mp3", "ogg", "m4a"],
            label_visibility="collapsed",
            help="Supports WAV, MP3, OGG, M4A formats",
        )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    analyze_clicked = st.button(
        "🔎 Analyze",
        type="primary",
        use_container_width=True,
        disabled=not backend_up,
    )
    st.caption("⌨️ Ctrl+Enter to analyze")


# ============================================================
# EMPTY STATE
# ============================================================
if not analyze_clicked and not st.session_state.get("last_result"):
    st.markdown("""
    <div style="text-align:center; padding:80px 20px; color:var(--text-secondary);" class="animate-in">
        <div style="font-size:4rem; margin-bottom:20px; filter:drop-shadow(0 0 20px rgba(6,182,212,0.3));">🔍</div>
        <h2 style="color:var(--text-primary); font-weight:700; margin-bottom:8px; font-size:1.6rem;">
            Forensic Intelligence Dashboard
        </h2>
        <p style="font-size:1.05rem; max-width:520px; margin:0 auto; line-height:1.7;">
            Paste text or upload media to start your first investigation.<br>
            TruthLens analyzes across
            <span style="color:var(--cyan); font-weight:600;">NLP</span>,
            <span style="color:var(--cyan); font-weight:600;">Image</span>,
            <span style="color:var(--cyan); font-weight:600;">Video</span>, and
            <span style="color:var(--cyan); font-weight:600;">Audio</span> modalities.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🚀 Next-Gen Features", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**🛡️ Security**")
            st.caption("Secure upload sandbox, privacy mode, data retention")
        with cols[1]:
            st.markdown("**📊 Operations**")
            st.caption("System health, trace IDs, observability")
        with cols[2]:
            st.markdown("**🔬 Research**")
            st.caption("Red team, drift detection, model comparison")


# ============================================================
# ANALYSIS EXECUTION
# ============================================================
def run_analysis(text_input, image_file, video_file, audio_file):
    """Run multimodal analysis with progress tracking."""
    progress = st.progress(0, text="📤 Preparing inputs…")

    files = {}
    data = {}
    if text_input and text_input.strip():
        data["text"] = text_input.strip()
        progress.progress(20, text="📝 Text analysis queued…")
    if image_file:
        files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
        progress.progress(20, text="🖼️ Image analysis queued…")
    if video_file:
        files["video"] = (video_file.name, video_file.getvalue(), video_file.type)
        progress.progress(20, text="🎬 Video analysis queued…")
    if audio_file:
        files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
        progress.progress(20, text="🔊 Audio analysis queued…")

    progress.progress(40, text="🔬 Analyzing across modalities…")

    try:
        resp = requests.post(f"{API_URL}/analyze", data=data, files=files, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        progress.progress(80, text="📊 Generating report…")
        progress.progress(100, text="✅ Analysis complete!")
        return result
    except requests.exceptions.ConnectionError:
        st.error("🔌 Could not connect to the TruthLens API. Is the backend running?")
        st.stop()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("detail", str(e))
        except Exception:
            error_detail = str(e)
        st.error(f"⚠️ API error: {error_detail}")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.stop()
    finally:
        _time.sleep(0.3)
        progress.empty()


if analyze_clicked:
    has_text = text_input and text_input.strip()
    has_media = image_file or video_file or audio_file
    if not has_text and not has_media:
        st.error("Please provide at least one input (text, image, video, or audio).")
    elif not backend_up:
        st.error("Backend is not running. Start it first.")
    else:
        result = run_analysis(text_input, image_file, video_file, audio_file)

        st.session_state.last_result = result
        st.session_state.last_image_file = image_file
        st.session_state.last_video_file = video_file
        st.session_state.last_audio_file = audio_file
        st.session_state.last_text_input = text_input

        if "results" not in st.session_state:
            st.session_state.results = []
        st.session_state.results.insert(0, result)

        st.toast(f"Analysis complete! Score: {result['threat_score']}/100", icon="✅")


# ============================================================
# RESULTS DISPLAY
# ============================================================
if st.session_state.get("last_result"):
    result = st.session_state.last_result
    text_input = st.session_state.get("last_text_input")
    image_file = st.session_state.get("last_image_file")
    video_file = st.session_state.get("last_video_file")
    audio_file = st.session_state.get("last_audio_file")

    score = result["threat_score"]
    verdict = result["verdict"]
    consistency = result.get("consistency", "unanimous")
    analysis_id = result.get("id", "")

    # --- Threat Overview ---
    col_gauge, col_verdict = st.columns([2, 1])

    with col_gauge:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 42, "color": "#f1f5f9", "family": "JetBrains Mono"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b", "tickfont": {"color": "#64748b"}},
                "bar": {"color": "#06b6d4", "thickness": 0.6},
                "bgcolor": "#1e293b",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 30], "color": "rgba(34, 197, 94, 0.12)"},
                    {"range": [30, 70], "color": "rgba(245, 158, 11, 0.12)"},
                    {"range": [70, 100], "color": "rgba(239, 68, 68, 0.12)"},
                ],
                "threshold": {
                    "line": {"color": "#06b6d4", "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        ))
        fig.update_layout(
            height=280,
            margin=dict(l=30, r=30, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#f1f5f9", "family": "Inter"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_verdict:
        verdict_css = {"Low": "verdict-low", "Review Needed": "verdict-review", "High Risk": "verdict-high"}
        verdict_icon = {"Low": "🟢", "Review Needed": "🟡", "High Risk": "🔴"}
        css_class = verdict_css.get(verdict, "verdict-review")
        icon = verdict_icon.get(verdict, "⚪")

        st.markdown(f"""
        <div class="animate-in">
            <div class="{css_class} verdict-badge">
                {icon} {verdict}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        st.metric("Threat Score", f"{score}/100")
        st.caption(f"Consistency: **{consistency}**")

        if score >= 30:
            st.markdown(f"""
            <div class="ops-card" style="margin-top:8px; border-color:var(--amber);">
                <span style="color:var(--amber); font-size:0.85rem; font-weight:500;">
                    ⚠️ Review recommended for this confidence level
                </span>
            </div>
            """, unsafe_allow_html=True)

    # --- Modality Breakdown ---
    st.markdown("### 📊 Modality Breakdown")
    breakdown = result.get("breakdown", {})

    mod_data = []
    for mod in ["text", "image", "video", "audio"]:
        detail = breakdown.get(mod)
        if detail and isinstance(detail, dict) and "label" in detail:
            mod_data.append({
                "modality": mod.upper(),
                "label": detail["label"],
                "confidence": detail.get("confidence", 0),
                "threat": detail.get("threat_contribution", 0),
                "weight": detail.get("weight", 0),
            })

    if mod_data:
        for d in mod_data:
            icon = {"TEXT": "📝", "IMAGE": "🖼️", "VIDEO": "🎬", "AUDIO": "🔊"}.get(d["modality"], "📄")
            label_color = "var(--crimson)" if d["label"] in ("fake", "cloned") else "var(--emerald)"
            label_chip = "chip-crimson" if d["label"] in ("fake", "cloned") else "chip-emerald"
            conf_pct = d["confidence"] * 100
            threat_pct = d["threat"] * 100

            st.markdown(f"""
            <div class="ops-card animate-in" style="display:flex; align-items:center; gap:16px;">
                <span style="font-size:1.5rem;">{icon}</span>
                <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="color:var(--text-primary); font-weight:600;">{d['modality']}</span>
                        <span class="chip {label_chip}">{d['label'].upper()}</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width:{conf_pct}%; background:{label_color};"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:4px;">
                        <span style="color:var(--text-tertiary); font-size:0.78rem; font-variant-numeric:tabular-nums;">
                            Confidence: {conf_pct:.0f}%
                        </span>
                        <span style="color:var(--text-tertiary); font-size:0.78rem; font-variant-numeric:tabular-nums;">
                            Threat: {threat_pct:.0f}%
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No modality results to display.")

    # --- Explanations ---
    st.markdown("### 🔍 Explanations")

    explain_tabs = st.tabs(["📝 Text", "🖼️ Image", "🎬 Video", "🔊 Audio"])

    with explain_tabs[0]:
        if text_input:
            if st.button("📝 Generate Text Explanation", key="explain_text_v3"):
                with st.spinner("Generating SHAP explanation…"):
                    try:
                        r = requests.post(
                            f"{API_URL}/predict/text/explain",
                            json={"text": text_input, "top_k": 10},
                            timeout=30,
                        )
                        if r.ok:
                            exp = r.json()
                            tokens = exp.get("tokens", [])
                            if tokens:
                                html = '<div style="display:flex; flex-wrap:wrap; gap:6px;">'
                                for t in tokens:
                                    attr = t.get("attribution", 0)
                                    is_positive = attr >= 0
                                    color = "var(--emerald)" if is_positive else "var(--crimson)"
                                    bg = "rgba(34, 197, 94, 0.12)" if is_positive else "rgba(239, 68, 68, 0.12)"
                                    size = max(0.7, min(1.4, abs(attr) * 3))
                                    html += f'<span style="background:{bg}; color:{color}; padding:4px 8px; border-radius:var(--radius-sm); font-size:{size}rem; font-weight:500;">{t.get("token", "?")}</span>'
                                html += "</div>"
                                st.markdown(html, unsafe_allow_html=True)
                            else:
                                st.json(exp)
                        else:
                            st.warning("Text explanation unavailable")
                    except Exception:
                        st.warning("Text explanation unavailable")
        else:
            st.info("Provide text input to see explanations.")

    with explain_tabs[1]:
        if image_file:
            if st.button("🖼️ Generate Image Explanation", key="explain_image_v3"):
                with st.spinner("Generating Grad-CAM heatmap…"):
                    try:
                        files_exp = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
                        r = requests.post(f"{API_URL}/predict/image/explain", files=files_exp, timeout=30)
                        if r.ok:
                            exp = r.json()
                            img_data = base64.b64decode(exp["heatmap_b64"])
                            st.image(img_data, caption="Grad-CAM Heatmap — Red regions indicate suspicious areas", use_container_width=True)
                        else:
                            st.warning("Image explanation unavailable")
                    except Exception:
                        st.warning("Image explanation unavailable")
        else:
            st.info("Upload an image to see Grad-CAM explanations.")

    with explain_tabs[2]:
        if video_file:
            if st.button("🎬 Generate Video Explanation", key="explain_video_v3"):
                with st.spinner("Generating temporal explanation…"):
                    try:
                        files_exp = {"file": (video_file.name, video_file.getvalue(), video_file.type)}
                        r = requests.post(f"{API_URL}/predict/video/explain", files=files_exp, timeout=60)
                        if r.ok:
                            exp = r.json()
                            frame_imp = exp.get("frame_importance", [])
                            if frame_imp:
                                frames = [f["frame"] for f in frame_imp]
                                imps = [f["importance"] for f in frame_imp]
                                fig_f = go.Figure(go.Bar(
                                    x=frames, y=imps,
                                    marker_color=["#ef4444" if i > 0.5 else "#22c55e" for i in imps],
                                    marker_line=dict(width=0),
                                ))
                                fig_f.update_layout(
                                    xaxis_title="Frame",
                                    yaxis_title="Importance",
                                    height=200,
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    font={"color": "#f1f5f9", "family": "Inter"},
                                    xaxis=dict(gridcolor="#334155"),
                                    yaxis=dict(gridcolor="#334155"),
                                )
                                st.plotly_chart(fig_f, use_container_width=True)
                        else:
                            st.warning("Video explanation unavailable")
                    except Exception:
                        st.warning("Video explanation unavailable")
        else:
            st.info("Upload a video to see frame-level explanations.")

    with explain_tabs[3]:
        if audio_file:
            if st.button("🔊 Generate Audio Explanation", key="explain_audio_v3"):
                with st.spinner("Generating frequency explanation…"):
                    try:
                        files_exp = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                        r = requests.post(f"{API_URL}/predict/audio/explain", files=files_exp, timeout=30)
                        if r.ok:
                            exp = r.json()
                            st.json(exp.get("top_coefficients", []))
                        else:
                            st.warning("Audio explanation unavailable")
                    except Exception:
                        st.warning("Audio explanation unavailable")
        else:
            st.info("Upload audio to see MFCC frequency explanations.")

    # --- Evidence Chain ---
    with st.expander("🔗 Evidence Chain & Audit Trail", expanded=False):
        col_ev, col_audit = st.columns(2)
        with col_ev:
            st.markdown("**Evidence Summary**")
            st.json({
                "analysis_id": analysis_id,
                "modalities_analyzed": list(breakdown.keys()),
                "consistency": consistency,
                "threat_score": score,
                "verdict": verdict,
            })
        with col_audit:
            st.markdown("**Investigation Details**")
            st.caption(f"ID: `{analysis_id}`")
            st.caption(f"Input types: {', '.join(result.get('input_types', []))}")
            st.caption(f"Timestamp: {result.get('timestamp', 'N/A')}")

    # --- Next-Gen Panel ---
    with st.expander("🚀 Next-Gen Intelligence", expanded=False):
        ng_cols = st.columns(2)
        with ng_cols[0]:
            st.markdown("**Uncertainty Assessment**")
            if st.button("Compute Uncertainty", key="uncertainty_btn_v2"):
                try:
                    r = requests.post(f"{API_URL}/nextgen/uncertainty", json={
                        "risk_score": score,
                        "model_confidence": 1 - score / 100,
                        "modality_count": len([m for m in ["text", "image", "video", "audio"] if breakdown.get(m)]),
                    }, timeout=10)
                    if r.ok:
                        unc = r.json()
                        level = unc.get("level", "UNKNOWN")
                        level_chip = {"LOW": "chip-emerald", "MEDIUM": "chip-amber", "HIGH": "chip-crimson", "CRITICAL": "chip-crimson"}.get(level, "chip-cyan")
                        st.markdown(f'<span class="chip {level_chip}">Level: {level}</span>', unsafe_allow_html=True)
                        st.caption(unc.get("recommendation", ""))
                        if unc.get("sources"):
                            for s in unc["sources"]:
                                st.caption(f"• {s}")
                except Exception:
                    st.warning("Uncertainty service unavailable")

            st.markdown("**Decision Matrix**")
            if st.button("Run Decision Matrix", key="decision_btn_v2"):
                try:
                    r = requests.post(f"{API_URL}/nextgen/decision", json={
                        "risk_score": score,
                        "evidence_strength": 0.5,
                        "model_confidence": 1 - score / 100,
                    }, timeout=10)
                    if r.ok:
                        dec = r.json()
                        st.markdown(f"**Assessment:** {dec.get('assessment', 'N/A')}")
                        st.caption(dec.get("rationale", ""))
                except Exception:
                    st.warning("Decision service unavailable")

        with ng_cols[1]:
            st.markdown("**Counterfactual Analysis**")
            if st.button("What Would Change?", key="counter_btn_v2"):
                try:
                    r = requests.post(f"{API_URL}/nextgen/counterfactuals", json={
                        "current_risk": score,
                        "evidence_strength": 0.3,
                        "model_confidence": 1 - score / 100,
                    }, timeout=10)
                    if r.ok:
                        cf = r.json()
                        st.caption("⚠️ These are sensitivity estimates, not guaranteed outcomes.")
                        for s in cf.get("scenarios", []):
                            delta = s.get("risk_delta", 0)
                            chip_class = "chip-emerald" if delta < 0 else "chip-crimson"
                            st.markdown(f"""
                            <div class="ops-card" style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:var(--text-primary); font-size:0.9rem;">{s.get('condition', '')}</span>
                                <span class="chip {chip_class}">Risk: {s.get('estimated_risk', 0):.0f} ({delta:+.0f})</span>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception:
                    st.warning("Counterfactual service unavailable")

    # --- Export ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    col_dl, col_spacer = st.columns([1, 4])
    with col_dl:
        if st.button("📄 Download Report"):
            try:
                r = requests.get(f"{API_URL}/analyze/{analysis_id}/report", timeout=30)
                if r.status_code == 200:
                    st.download_button(
                        label="Save Report",
                        data=r.content,
                        file_name=f"truthlens_report_{analysis_id[:8]}.pdf",
                        mime="application/pdf",
                    )
                    st.toast("Report downloaded!", icon="📄")
                else:
                    st.warning("Report not available yet.")
            except Exception:
                st.warning("Report not available yet.")

    st.markdown("""
    <div style="text-align:center; padding:16px; color:var(--text-tertiary); font-size:0.8rem; border-top:1px solid var(--border-default); margin-top:16px;">
        AI-generated analysis — verify independently. TruthLens v1.0.0
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# HISTORY PANEL
# ============================================================
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("### 📋 Recent Analyses")

history = []
try:
    resp = requests.get(f"{API_URL}/analyses?limit=10", timeout=5)
    if resp.ok:
        history = resp.json()
except Exception:
    pass

if not history and "results" in st.session_state:
    history = [
        {"id": r["id"], "verdict": r["verdict"], "threat_score": r["threat_score"],
         "input_types": list(k for k, v in r.get("breakdown", {}).items()
                           if isinstance(v, dict) and "label" in v)}
        for r in st.session_state.results[:10]
    ]

if history:
    for entry in history:
        verdict = entry.get("verdict", "?")
        score_val = entry.get("threat_score", 0)
        inputs = entry.get("input_types", [])
        icon = "🟢" if verdict == "Low" else "🟡" if verdict == "Review Needed" else "🔴"
        with st.expander(f"{icon} **{verdict}** — Score: {score_val}/100 — {', '.join(inputs)}"):
            st.json(entry)
else:
    st.info("No analyses yet. Run your first analysis above!")
