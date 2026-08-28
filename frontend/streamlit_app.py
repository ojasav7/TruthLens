"""
TruthLens Dashboard — Dark Ops-Center Redesign
Forensic intelligence dashboard for multimodal misinformation detection.
"""

import io
import os
import base64
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
# DARK OPS-CENTER CSS
# ============================================================
st.markdown("""
<style>
/* === Global === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-primary: #0f172a;
    --bg-surface: #1e293b;
    --bg-card: #1e293b;
    --border: #334155;
    --cyan: #06b6d4;
    --cyan-glow: rgba(6, 182, 212, 0.3);
    --crimson: #ef4444;
    --amber: #f59e0b;
    --emerald: #22c55e;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
}

/* Fix Streamlit defaults for dark theme */
.stApp { background-color: var(--bg-primary); }
section[data-testid="stSidebar"] { background-color: #0c1322; }
div[data-testid="stVerticalBlock"] > div { margin-bottom: 0.5rem; }

/* Focus rings — WCAG 2.2 AA */
:focus-visible {
    outline: 2px solid var(--cyan) !important;
    outline-offset: 2px !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-secondary);
    padding: 8px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(6, 182, 212, 0.15) !important;
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
}

/* Verdict pill badges */
.verdict-pill {
    display: inline-block;
    padding: 8px 24px;
    border-radius: 50px;
    font-size: 1.4rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-align: center;
}
.verdict-low {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    border: 2px solid #22c55e;
}
.verdict-review {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 2px solid #f59e0b;
}
.verdict-high {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 2px solid #ef4444;
}

/* Status dot */
.status-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 6px;
}
.status-dot.green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-dot.red { background: #ef4444; box-shadow: 0 0 6px #ef4444; }

/* Pulse animation for high-risk */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.3); }
    50% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
}
.pulse-danger { animation: pulse-glow 2s ease-in-out infinite; }

/* Progress bar override */
.stProgress > div > div > div > div {
    background: var(--cyan) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-weight: 600;
}

/* Card-like containers */
.ops-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}

/* Reduce motion for accessibility */
@media (prefers-reduced-motion: reduce) {
    @keyframes pulse-glow { 0%, 100% { box-shadow: none; } }
    * { animation-duration: 0.01ms !important; }
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
<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #334155; margin-bottom:16px;">
    <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.5rem;">🔍</span>
        <span style="font-size:1.3rem; font-weight:700; color:#f1f5f9; letter-spacing:0.05em;">TRUTHLENS</span>
        <span style="background:#1e293b; border:1px solid #334155; border-radius:6px; padding:2px 8px; font-size:0.75rem; color:#94a3b8;">v1.0.0</span>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
        <span style="color:#94a3b8; font-size:0.85rem;"><span class="status-dot {status_color}"></span>{status_text}</span>
        <a href="{API_URL}/docs" target="_blank" style="color:#06b6d4; text-decoration:none; font-size:0.85rem;">API Docs ↗</a>
    </div>
</div>
""", unsafe_allow_html=True)

if not backend_up:
    st.warning("⚠️ Backend not running. Start with: `uvicorn backend.main:app --reload`")


# ============================================================
# SIDEBAR — INPUT PANEL WITH TABS
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
            placeholder="Paste suspicious news, headline, or social media post...",
            height=150,
            label_visibility="collapsed",
        )
        if text_input:
            st.caption(f"📊 {len(text_input)} characters")

    with input_tabs[1]:
        image_file = st.file_uploader(
            "Upload image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )

    with input_tabs[2]:
        video_file = st.file_uploader(
            "Upload video",
            type=["mp4", "avi", "mov", "webm"],
            label_visibility="collapsed",
        )

    with input_tabs[3]:
        audio_file = st.file_uploader(
            "Upload audio",
            type=["wav", "mp3", "ogg", "m4a"],
            label_visibility="collapsed",
        )

    st.markdown("---")
    analyze_clicked = st.button(
        "🔎 Analyze",
        type="primary",
        use_container_width=True,
        disabled=not backend_up,
    )
    st.caption("⌨️ Ctrl+Enter to analyze")


# ============================================================
# MAIN AREA — EMPTY STATE
# ============================================================
if not analyze_clicked and not st.session_state.get("last_result"):
    st.markdown("""
    <div style="text-align:center; padding:80px 20px; color:#94a3b8;">
        <div style="font-size:4rem; margin-bottom:16px;">🔍</div>
        <h2 style="color:#f1f5f9; font-weight:700; margin-bottom:8px;">Forensic Intelligence Dashboard</h2>
        <p style="font-size:1.1rem; max-width:500px; margin:0 auto;">
            Paste text or upload media to start your first investigation.<br>
            TruthLens analyzes across <strong style="color:#06b6d4;">NLP</strong>, <strong style="color:#06b6d4;">Image</strong>, <strong style="color:#06b6d4;">Video</strong>, and <strong style="color:#06b6d4;">Audio</strong> modalities.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick access to next-gen features
    st.markdown("---")
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
    progress = st.progress(0, text="📤 Preparing inputs...")

    files = {}
    data = {}
    if text_input and text_input.strip():
        data["text"] = text_input.strip()
        progress.progress(20, text="📝 Text analysis queued...")
    if image_file:
        files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
        progress.progress(20, text="🖼️ Image analysis queued...")
    if video_file:
        files["video"] = (video_file.name, video_file.getvalue(), video_file.type)
        progress.progress(20, text="🎬 Video analysis queued...")
    if audio_file:
        files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
        progress.progress(20, text="🔊 Audio analysis queued...")

    progress.progress(40, text="🔬 Analyzing across modalities...")

    try:
        resp = requests.post(f"{API_URL}/analyze", data=data, files=files, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        progress.progress(80, text="📊 Generating report...")
        progress.progress(100, text="✅ Analysis complete!")
        return result
    except requests.exceptions.ConnectionError:
        st.error("🔌 Could not connect to the TruthLens API. Is the backend running?")
        st.stop()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get('detail', str(e))
        except Exception:
            error_detail = str(e)
        st.error(f"⚠️ API error: {error_detail}")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.stop()
    finally:
        import time
        time.sleep(0.3)
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

        # Store in session state
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
# RESULTS DISPLAY (runs on EVERY rerun from session state)
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
        # Dynamic gauge colors based on theme
        gauge_class = "pulse-danger" if score >= 70 else ""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 40, "color": "#f1f5f9"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": "#06b6d4"},
                "bgcolor": "#1e293b",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 30], "color": "rgba(34, 197, 94, 0.2)"},
                    {"range": [30, 70], "color": "rgba(245, 158, 11, 0.2)"},
                    {"range": [70, 100], "color": "rgba(239, 68, 68, 0.2)"},
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
            font={"color": "#f1f5f9"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_verdict:
        verdict_class = {"Low": "verdict-low", "Review Needed": "verdict-review", "High Risk": "verdict-high"}
        verdict_icon = {"Low": "🟢", "Review Needed": "🟡", "High Risk": "🔴"}
        css_class = verdict_class.get(verdict, "verdict-review")
        icon = verdict_icon.get(verdict, "⚪")

        st.markdown(f"""
        <div class="{css_class} verdict-pill">
            {icon} {verdict}
        </div>
        """, unsafe_allow_html=True)

        st.metric("Threat Score", f"{score}/100")
        st.caption(f"Consistency: **{consistency}**")

        # Next-gen: quick uncertainty preview
        if score >= 30:
            st.markdown(f"""<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px; margin-top:8px;">
                <span style="color:#94a3b8; font-size:0.8rem;">⚠️ Review recommended for this confidence level</span>
            </div>""", unsafe_allow_html=True)

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
        # Horizontal cards with progress bars
        for d in mod_data:
            icon = {"TEXT": "📝", "IMAGE": "🖼️", "VIDEO": "🎬", "AUDIO": "🔊"}.get(d["modality"], "📄")
            label_color = "#ef4444" if d["label"] in ("fake", "cloned") else "#22c55e"
            conf_pct = d["confidence"] * 100
            threat_pct = d["threat"] * 100

            st.markdown(f"""
            <div class="ops-card" style="display:flex; align-items:center; gap:16px;">
                <span style="font-size:1.5rem;">{icon}</span>
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="color:#f1f5f9; font-weight:600;">{d['modality']}</span>
                        <span style="color:{label_color}; font-weight:600;">{d['label'].upper()}</span>
                    </div>
                    <div style="background:#0f172a; border-radius:4px; height:8px; overflow:hidden;">
                        <div style="width:{conf_pct}%; background:{label_color}; height:100%; border-radius:4px;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:4px;">
                        <span style="color:#94a3b8; font-size:0.8rem;">Confidence: {conf_pct:.0f}%</span>
                        <span style="color:#94a3b8; font-size:0.8rem;">Threat: {threat_pct:.0f}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No modality results to display.")

    # --- Explanations (Tabbed) ---
    st.markdown("### 🔍 Explanations")

    explain_tabs = st.tabs(["📝 Text", "🖼️ Image", "🎬 Video", "🔊 Audio"])

    with explain_tabs[0]:
        if text_input:
            if st.button("📝 Generate Text Explanation", key="explain_text_v2"):
                with st.spinner("Generating SHAP explanation..."):
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
                                # Color-coded token display
                                html = '<div style="display:flex; flex-wrap:wrap; gap:6px;">'
                                for t in tokens:
                                    color = "#ef4444" if t.get("attribution", 0) < 0 else "#22c55e"
                                    size = max(0.7, min(1.5, abs(t.get("attribution", 0)) * 3))
                                    html += f'<span style="background:rgba({("239,68,68" if t.get("attribution", 0) < 0 else "34,197,94")},0.15); color:{color}; padding:4px 8px; border-radius:6px; font-size:{size}rem;">{t.get("token", "?")}</span>'
                                html += '</div>'
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
            if st.button("🖼️ Generate Image Explanation", key="explain_image_v2"):
                with st.spinner("Generating Grad-CAM heatmap..."):
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
            if st.button("🎬 Generate Video Explanation", key="explain_video_v2"):
                with st.spinner("Generating temporal explanation..."):
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
                                ))
                                fig_f.update_layout(
                                    xaxis_title="Frame",
                                    yaxis_title="Importance",
                                    height=200,
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    font={"color": "#f1f5f9"},
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
            if st.button("🔊 Generate Audio Explanation", key="explain_audio_v2"):
                with st.spinner("Generating frequency explanation..."):
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

    # --- Evidence Chain (collapsible) ---
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
            if st.button("Compute Uncertainty", key="uncertainty_btn"):
                try:
                    r = requests.post(f"{API_URL}/nextgen/uncertainty", json={
                        "risk_score": score,
                        "model_confidence": 1 - score / 100,
                        "modality_count": len([m for m in ["text", "image", "video", "audio"] if breakdown.get(m)]),
                    }, timeout=10)
                    if r.ok:
                        unc = r.json()
                        level_colors = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#ef4444", "CRITICAL": "#ef4444"}
                        level = unc.get("level", "UNKNOWN")
                        st.markdown(f"**Level:** :red[{level}]" if level in ("HIGH", "CRITICAL") else f"**Level:** {level}")
                        st.caption(unc.get("recommendation", ""))
                        if unc.get("sources"):
                            for s in unc["sources"]:
                                st.caption(f"• {s}")
                except Exception:
                    st.warning("Uncertainty service unavailable")

            st.markdown("**Decision Matrix**")
            if st.button("Run Decision Matrix", key="decision_btn"):
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
            if st.button("What Would Change?", key="counter_btn"):
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
                            color = "#22c55e" if delta < 0 else "#ef4444"
                            st.markdown(f"""
                            <div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:10px; margin:6px 0;">
                                <span style="color:#f1f5f9;">{s.get('condition', '')}</span><br>
                                <span style="color:{color}; font-weight:600;">Risk: {s.get('estimated_risk', 0):.0f} ({delta:+.0f})</span>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception:
                    st.warning("Counterfactual service unavailable")

    # --- Export & Footer ---
    st.markdown("---")
    col_dl, col_share, col_spacer = st.columns([1, 1, 3])
    with col_dl:
        if st.button("📄 Download PDF Report"):
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
    <div style="text-align:center; padding:16px; color:#64748b; font-size:0.8rem; border-top:1px solid #334155; margin-top:16px;">
        AI-generated analysis — verify independently. TruthLens v1.0.0
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# HISTORY PANEL
# ============================================================
st.markdown("---")
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
