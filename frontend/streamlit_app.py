"""
TruthLens Dashboard — Phase 6
Streamlit frontend for multimodal misinformation detection.
"""

import io
import os
import requests
import streamlit as st
import plotly.graph_objects as go
from PIL import Image

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="TruthLens", page_icon="🔍", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
.verdict-low { color: #22c55e; font-size: 2rem; font-weight: bold; }
.verdict-review { color: #f59e0b; font-size: 2rem; font-weight: bold; }
.verdict-high { color: #ef4444; font-size: 2rem; font-weight: bold; }
.stMetric > div { background: #f8fafc; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 TruthLens")
st.caption("AI-Powered Multimodal Misinformation & Threat Detection")

# --- Check backend health ---
def check_backend():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.ok
    except Exception:
        return False

backend_up = check_backend()
if not backend_up:
    st.warning("⚠️ Backend not running. Start with: `uvicorn backend.main:app --reload`")

# --- Layout: Sidebar for inputs, main area for results ---
with st.sidebar:
    st.header("📝 Inputs")
    text_input = st.text_area(
        "Text to analyze",
        placeholder="Paste suspicious news, headline, or social media post here...",
        height=120,
    )
    image_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png", "webp"])
    video_file = st.file_uploader("Upload video", type=["mp4", "avi", "mov", "webm"])
    audio_file = st.file_uploader("Upload audio", type=["wav", "mp3", "ogg", "m4a"])

    analyze_clicked = st.button("🔎 Analyze", type="primary", use_container_width=True)

# --- Analysis ---
if analyze_clicked:
    if not text_input and not image_file and not video_file and not audio_file:
        st.error("Please provide at least one input (text, image, video, or audio).")
    elif not backend_up:
        st.error("Backend is not running. Start it first.")
    else:
        with st.spinner("Analyzing across all modalities..."):
            files = {}
            data = {}
            if text_input:
                data["text"] = text_input
            if image_file:
                files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
            if video_file:
                files["video"] = (video_file.name, video_file.getvalue(), video_file.type)
            if audio_file:
                files["audio"] = (audio_file.name, audio_file.getvalue(), audio_file.type)

            try:
                resp = requests.post(f"{API_URL}/analyze", data=data, files=files, timeout=120)
                resp.raise_for_status()
                result = resp.json()
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the TruthLens API.")
                st.stop()
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()

        # --- Store result + files in session for explain buttons ---
        st.session_state.last_result = result
        st.session_state.last_image_file = image_file
        st.session_state.last_video_file = video_file
        st.session_state.last_audio_file = audio_file
        st.session_state.last_text_input = text_input

        if "results" not in st.session_state:
            st.session_state.results = []
        st.session_state.results.insert(0, result)

        # --- Results ---
        st.success("Analysis complete!")

        score = result["threat_score"]
        verdict = result["verdict"]
        consistency = result.get("consistency", "unanimous")

        # Top row: Gauge + Verdict
        col_gauge, col_verdict = st.columns([2, 1])

        with col_gauge:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "/100", "font": {"size": 36}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#1e293b"},
                    "steps": [
                        {"range": [0, 30], "color": "#dcfce7"},
                        {"range": [30, 70], "color": "#fef9c3"},
                        {"range": [70, 100], "color": "#fee2e2"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": score,
                    },
                },
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_verdict:
            verdict_color = {"Low": "green", "Review Needed": "orange", "High Risk": "red"}
            color = verdict_color.get(verdict, "gray")
            st.markdown(f'<div class="verdict-{color}">{verdict}</div>', unsafe_allow_html=True)
            st.metric("Threat Score", f"{score}")
            st.caption(f"Consistency: **{consistency}**")

        # --- Modality Breakdown ---
        st.subheader("📊 Modality Breakdown")
        breakdown = result.get("breakdown", {})

        mod_data = []
        for mod in ["text", "image", "video", "audio"]:
            detail = breakdown.get(mod)
            if detail and isinstance(detail, dict) and "label" in detail:
                mod_data.append({
                    "Modality": mod.upper(),
                    "Label": detail["label"],
                    "Confidence": detail.get("confidence", 0),
                    "Threat": detail.get("threat_contribution", 0),
                    "Weight": detail.get("weight", 0),
                })

        if mod_data:
            # Bar chart of threat contributions
            labels = [d["Modality"] for d in mod_data]
            threats = [d["Threat"] for d in mod_data]
            bar_colors = ["#ef4444" if d["Label"] in ("fake", "cloned") else "#22c55e" for d in mod_data]

            fig_bar = go.Figure(go.Bar(
                x=labels, y=threats,
                marker_color=bar_colors,
                text=[f"{d['Label']} ({d['Confidence']:.0%})" for d in mod_data],
                textposition="auto",
            ))
            fig_bar.update_layout(
                yaxis_title="Threat Contribution",
                height=300,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Detail cards
            cols = st.columns(len(mod_data))
            for col, d in zip(cols, mod_data):
                with col:
                    icon = "📝" if d["Modality"] == "TEXT" else "🖼️" if d["Modality"] == "IMAGE" else "🎬" if d["Modality"] == "VIDEO" else "🔊"
                    st.metric(
                        f"{icon} {d['Modality']}",
                        f"{d['Label']}",
                        f"{d['Confidence']:.1%} conf",
                    )
        else:
            st.info("No modality results to display.")

        # --- Explain buttons ---
        st.subheader("🔍 Explanations")
        explain_cols = st.columns(4)

        if text_input:
            with explain_cols[0]:
                if st.button("📝 Explain Text", key="explain_text"):
                    with st.spinner("Generating SHAP explanation..."):
                        try:
                            r = requests.post(
                                f"{API_URL}/predict/text/explain",
                                json={"text": text_input, "top_k": 5},
                                timeout=30,
                            )
                            if r.ok:
                                exp = r.json()
                                st.json(exp.get("tokens", []))
                            else:
                                st.warning("Text explanation unavailable")
                        except Exception:
                            st.warning("Text explanation unavailable")

        if image_file:
            with explain_cols[1]:
                if st.button("🖼️ Explain Image", key="explain_image"):
                    with st.spinner("Generating Grad-CAM heatmap..."):
                        try:
                            files_exp = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
                            r = requests.post(f"{API_URL}/predict/image/explain", files=files_exp, timeout=30)
                            if r.ok:
                                exp = r.json()
                                import base64
                                img_data = base64.b64decode(exp["heatmap_b64"])
                                st.image(img_data, caption="Grad-CAM Heatmap", use_container_width=True)
                            else:
                                st.warning("Image explanation unavailable")
                        except Exception:
                            st.warning("Image explanation unavailable")

        if video_file:
            with explain_cols[2]:
                if st.button("🎬 Explain Video", key="explain_video"):
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
                                    fig_f = go.Figure(go.Bar(x=frames, y=imps, marker_color="#6366f1"))
                                    fig_f.update_layout(xaxis_title="Frame", yaxis_title="Importance", height=200)
                                    st.plotly_chart(fig_f, use_container_width=True)
                            else:
                                st.warning("Video explanation unavailable")
                        except Exception:
                            st.warning("Video explanation unavailable")

        if audio_file:
            with explain_cols[3]:
                if st.button("🔊 Explain Audio", key="explain_audio"):
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

        # --- Download Report ---
        st.divider()
        col_dl1, col_dl2 = st.columns([1, 3])
        with col_dl1:
            if st.button("📄 Download PDF Report"):
                try:
                    r = requests.get(f"{API_URL}/analyze/{result['id']}/report", timeout=30)
                    if r.status_code == 200:
                        st.download_button(
                            label="Save Report",
                            data=r.content,
                            file_name=f"truthlens_report_{result['id'][:8]}.pdf",
                            mime="application/pdf",
                        )
                    else:
                        st.warning("Report not available yet.")
                except Exception:
                    st.warning("Report not available yet.")

# ============================================================
# Results + Explain + Download — render from session state
# This block runs on EVERY rerun, not just when analyze_clicked.
# This is what makes the explain buttons actually work.
# ============================================================
if not analyze_clicked and st.session_state.get("last_result"):
    result = st.session_state.last_result
    text_input = st.session_state.get("last_text_input")
    image_file = st.session_state.get("last_image_file")
    video_file = st.session_state.get("last_video_file")
    audio_file = st.session_state.get("last_audio_file")

    st.success("Analysis complete!")

    score = result["threat_score"]
    verdict = result["verdict"]
    consistency = result.get("consistency", "unanimous")

    col_gauge, col_verdict = st.columns([2, 1])
    with col_gauge:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#1e293b"},
                "steps": [
                    {"range": [0, 30], "color": "#dcfce7"},
                    {"range": [30, 70], "color": "#fef9c3"},
                    {"range": [70, 100], "color": "#fee2e2"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_verdict:
        verdict_color = {"Low": "green", "Review Needed": "orange", "High Risk": "red"}
        color = verdict_color.get(verdict, "gray")
        st.markdown(f'<div class="verdict-{color}">{verdict}</div>', unsafe_allow_html=True)
        st.metric("Threat Score", f"{score}")
        st.caption(f"Consistency: **{consistency}**")

    st.subheader("📊 Modality Breakdown")
    breakdown = result.get("breakdown", {})
    mod_data = []
    for mod in ["text", "image", "video", "audio"]:
        detail = breakdown.get(mod)
        if detail and isinstance(detail, dict) and "label" in detail:
            mod_data.append({
                "Modality": mod.upper(),
                "Label": detail["label"],
                "Confidence": detail.get("confidence", 0),
                "Threat": detail.get("threat_contribution", 0),
                "Weight": detail.get("weight", 0),
            })
    if mod_data:
        labels = [d["Modality"] for d in mod_data]
        threats = [d["Threat"] for d in mod_data]
        bar_colors = ["#ef4444" if d["Label"] in ("fake", "cloned") else "#22c55e" for d in mod_data]
        fig_bar = go.Figure(go.Bar(
            x=labels, y=threats, marker_color=bar_colors,
            text=[f"{d['Label']} ({d['Confidence']:.0%})" for d in mod_data],
            textposition="auto",
        ))
        fig_bar.update_layout(yaxis_title="Threat Contribution", height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

        cols = st.columns(len(mod_data))
        for col, d in zip(cols, mod_data):
            with col:
                icon = "📝" if d["Modality"] == "TEXT" else "🖼️" if d["Modality"] == "IMAGE" else "🎬" if d["Modality"] == "VIDEO" else "🔊"
                st.metric(f"{icon} {d['Modality']}", f"{d['Label']}", f"{d['Confidence']:.1%} conf")

    # --- Explain buttons (NOW THEY WORK because this runs on rerun) ---
    st.subheader("🔍 Explanations")
    explain_cols = st.columns(4)

    if text_input:
        with explain_cols[0]:
            if st.button("📝 Explain Text", key="explain_text"):
                with st.spinner("Generating SHAP explanation..."):
                    try:
                        r = requests.post(f"{API_URL}/predict/text/explain", json={"text": text_input, "top_k": 5}, timeout=30)
                        if r.ok:
                            st.json(r.json().get("tokens", []))
                        else:
                            st.warning("Text explanation unavailable")
                    except Exception:
                        st.warning("Text explanation unavailable")

    if image_file:
        with explain_cols[1]:
            if st.button("🖼️ Explain Image", key="explain_image"):
                with st.spinner("Generating Grad-CAM heatmap..."):
                    try:
                        files_exp = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
                        r = requests.post(f"{API_URL}/predict/image/explain", files=files_exp, timeout=30)
                        if r.ok:
                            import base64
                            img_data = base64.b64decode(r.json()["heatmap_b64"])
                            st.image(img_data, caption="Grad-CAM Heatmap", use_container_width=True)
                        else:
                            st.warning("Image explanation unavailable")
                    except Exception:
                        st.warning("Image explanation unavailable")

    if video_file:
        with explain_cols[2]:
            if st.button("🎬 Explain Video", key="explain_video"):
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
                                fig_f = go.Figure(go.Bar(x=frames, y=imps, marker_color="#6366f1"))
                                fig_f.update_layout(xaxis_title="Frame", yaxis_title="Importance", height=200)
                                st.plotly_chart(fig_f, use_container_width=True)
                        else:
                            st.warning("Video explanation unavailable")
                    except Exception:
                        st.warning("Video explanation unavailable")

    if audio_file:
        with explain_cols[3]:
            if st.button("🔊 Explain Audio", key="explain_audio"):
                with st.spinner("Generating frequency explanation..."):
                    try:
                        files_exp = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                        r = requests.post(f"{API_URL}/predict/audio/explain", files=files_exp, timeout=30)
                        if r.ok:
                            st.json(r.json().get("top_coefficients", []))
                        else:
                            st.warning("Audio explanation unavailable")
                    except Exception:
                        st.warning("Audio explanation unavailable")

    # --- Download Report ---
    st.divider()
    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        if st.button("📄 Download PDF Report"):
            try:
                r = requests.get(f"{API_URL}/analyze/{result['id']}/report", timeout=30)
                if r.status_code == 200:
                    st.download_button(label="Save Report", data=r.content,
                                       file_name=f"truthlens_report_{result['id'][:8]}.pdf", mime="application/pdf")
                else:
                    st.warning("Report not available yet.")
            except Exception:
                st.warning("Report not available yet.")

# --- History ---
st.divider()
st.subheader("📋 Recent Analyses")

# Try API first, fall back to session state
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
        score = entry.get("threat_score", 0)
        inputs = entry.get("input_types", [])
        icon = "🟢" if verdict == "Low" else "🟡" if verdict == "Review Needed" else "🔴"
        with st.expander(f"{icon} **{verdict}** — Score: {score}/100 — {', '.join(inputs)}"):
            st.json(entry)
else:
    st.info("No analyses yet. Run your first analysis above!")
