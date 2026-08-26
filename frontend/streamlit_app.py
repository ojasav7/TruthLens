"""
TruthLens Dashboard — Phase 6
Streamlit frontend for multimodal misinformation detection.
"""

import io
import requests
import streamlit as st
from PIL import Image

API_URL = st.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="TruthLens", page_icon="🔍", layout="wide")
st.title("🔍 TruthLens — Misinformation Detection")
st.markdown("Upload text, images, video, or audio to analyze for misinformation risk.")

# --- Input Section ---
st.sidebar.header("📝 Inputs")
text_input = st.sidebar.text_area("Text to analyze", placeholder="Paste suspicious news text here...")
image_file = st.sidebar.file_uploader("Upload image", type=["jpg", "jpeg", "png", "webp"])
video_file = st.sidebar.file_uploader("Upload video", type=["mp4", "avi", "mov", "webm"])
audio_file = st.sidebar.file_uploader("Upload audio", type=["wav", "mp3", "ogg", "m4a"])

# --- Analyze Button ---
if st.button("🔎 Analyze", type="primary", use_container_width=True):
    if not text_input and not image_file and not video_file and not audio_file:
        st.error("Please provide at least one input (text, image, video, or audio).")
    else:
        with st.spinner("Analyzing..."):
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
                st.error("❌ Could not connect to the TruthLens API. Is the backend running?")
                st.stop()
            except Exception as e:
                st.error(f"❌ API error: {e}")
                st.stop()

        # --- Results Section ---
        st.success("Analysis complete!")

        # Threat Score Gauge
        col1, col2 = st.columns([1, 2])
        with col1:
            score = result["threat_score"]
            verdict = result["verdict"]
            color = "green" if verdict == "Low" else "orange" if verdict == "Review Needed" else "red"
            st.metric(label="Threat Score", value=f"{score}/100")
            st.markdown(f"### :{color}[{verdict}]")

        with col2:
            st.subheader("Modality Breakdown")
            breakdown = result.get("breakdown", {})
            for mod in ["text", "image", "video", "audio"]:
                detail = breakdown.get(mod)
                if detail and isinstance(detail, dict) and "label" in detail:
                    label = detail["label"]
                    conf = detail.get("confidence", 0)
                    bar_color = "red" if label in ("fake", "cloned") else "green"
                    st.markdown(f"**{mod.upper()}**: {label} ({conf:.1%})")
                    st.progress(conf)

        # Download report
        st.divider()
        if st.button("📄 Download PDF Report"):
            try:
                report_resp = requests.get(
                    f"{API_URL}/analyze/{result['id']}/report", timeout=30
                )
                if report_resp.status_code == 200:
                    st.download_button(
                        label="Save Report",
                        data=report_resp.content,
                        file_name=f"truthlens_report_{result['id'][:8]}.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.warning("Report generation not available yet.")
            except Exception:
                st.warning("Report generation not available yet.")

# --- History ---
st.divider()
st.subheader("📋 Recent Analyses")
try:
    resp = requests.get(f"{API_URL}/analyses?limit=10", timeout=10)
    if resp.ok:
        history = resp.json()
        if history:
            for entry in history:
                with st.expander(
                    f"**{entry['verdict']}** — Score: {entry['threat_score']}/100 — "
                    f"Inputs: {', '.join(entry['input_types'])}"
                ):
                    st.json(entry)
        else:
            st.info("No analyses yet. Run your first analysis above!")
except Exception:
    st.info("Could not load history (backend may not be running).")
