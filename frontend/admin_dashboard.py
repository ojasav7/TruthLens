"""
TruthLens Admin Dashboard — Security, Operations, Research
Full admin interface for system management.
"""

import os
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="TruthLens Admin", page_icon="🛡️", layout="wide")

# Dark theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background-color: #0f172a; }
section[data-testid="stSidebar"] { background-color: #0c1322; }
div[data-testid="stMetric"] { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; }
:focus-visible { outline: 2px solid #06b6d4 !important; outline-offset: 2px !important; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ TruthLens Admin Dashboard")

# Auth check
token = st.session_state.get("auth_token", "")
if not token:
    st.markdown("### 🔐 Login")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username", value="admin")
    with col2:
        password = st.text_input("Password", type="password", value="admin")
    if st.button("Login", type="primary"):
        try:
            resp = requests.post(f"{API_URL}/platform/auth/login", json={"username": username, "password": password}, timeout=5)
            if resp.ok:
                st.session_state.auth_token = resp.json()["token"]
                st.session_state.user_role = "admin"
                st.rerun()
            else:
                st.error("Invalid credentials")
        except Exception as e:
            st.error(f"Connection error: {e}")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

# Sidebar navigation
page = st.sidebar.radio("Navigation", [
    "📊 System Health",
    "🔍 Security",
    "📈 Observability",
    "🔬 Research",
    "🤖 Model Management",
    "📱 Platform",
], index=0)

# ============================================================
# SYSTEM HEALTH
# ============================================================
if page == "📊 System Health":
    st.header("📊 System Health")

    try:
        resp = requests.get(f"{API_URL}/nextgen/health/detailed", headers=headers, timeout=10)
        if resp.ok:
            health = resp.json()
            # Overall status
            status = health["overall_status"]
            color = {"HEALTHY": "🟢", "DEGRADED": "🟡", "UNAVAILABLE": "🔴"}.get(status, "⚪")
            st.markdown(f"## {color} Overall Status: **{status}**")

            # Metrics row
            m = health["metrics"]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Requests", m.get("request_count", 0))
            col2.metric("Errors", m.get("error_count", 0))
            col3.metric("Avg Latency", f"{m.get('avg_latency_ms', 0):.0f}ms")
            col4.metric("Uptime", f"{m.get('uptime_seconds', 0):.0f}s")

            # Components
            st.subheader("Components")
            for comp in health["components"]:
                icon = {"HEALTHY": "🟢", "DEGRADED": "🟡", "UNAVAILABLE": "🔴", "UNKNOWN": "⚪"}.get(comp["status"], "⚪")
                st.markdown(f"{icon} **{comp['name']}** — {comp['detail']}")
        else:
            st.error("Could not fetch health data")
    except Exception as e:
        st.error(f"Backend not reachable: {e}")

    # Deployment info
    try:
        resp = requests.get(f"{API_URL}/platform/deployment/info", headers=headers, timeout=5)
        if resp.ok:
            st.subheader("Deployment")
            info = resp.json()
            st.json(info)
    except Exception:
        pass

# ============================================================
# SECURITY
# ============================================================
elif page == "🔍 Security":
    st.header("🔍 Security Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["🛡️ Sandbox", "🔒 Privacy", "📋 Events", "📊 Stats"])

    with tab1:
        st.subheader("Upload Sandbox")
        uploaded = st.file_uploader("Test upload validation", type=["jpg", "jpeg", "png", "webp", "mp4", "wav", "mp3"])
        if uploaded:
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            resp = requests.post(f"{API_URL}/nextgen/sandbox/validate", files=files, timeout=10)
            if resp.ok:
                result = resp.json()
                if result["valid"]:
                    st.success(f"✅ Valid — {result['file_type']} ({result['file_size'] / 1024:.0f}KB)")
                else:
                    st.error(f"❌ Invalid — {result.get('errors', [])}")
                st.json(result)

        st.subheader("Quarantine List")
        st.caption("Files flagged as suspicious during sandbox validation")

    with tab2:
        st.subheader("Privacy Mode")
        resp = requests.get(f"{API_URL}/nextgen/privacy/info", headers=headers, timeout=5)
        if resp.ok:
            info = resp.json()
            st.markdown("**Stored long-term:**")
            for item in info.get("stored", []):
                st.markdown(f"  • {item}")
            st.markdown("**Temporary:**")
            for item in info.get("temporary", []):
                st.markdown(f"  • {item}")
            st.info(info.get("retention_summary", ""))

        st.subheader("Data Retention Policies")
        resp = requests.get(f"{API_URL}/nextgen/retention/policies", headers=headers, timeout=5)
        if resp.ok:
            policies = resp.json()
            for name, policy in policies.items():
                st.markdown(f"**{name}**: {policy['retention_days']} days — {policy['action']}")

    with tab3:
        st.subheader("Security Events")
        resp = requests.get(f"{API_URL}/nextgen/security/events?limit=50", headers=headers, timeout=5)
        if resp.ok:
            events = resp.json()
            if events:
                for ev in events[-20:]:
                    sev_color = {"CRITICAL": "🔴", "WARN": "🟡", "INFO": "🔵"}.get(ev.get("severity", ""), "⚪")
                    st.markdown(f"{sev_color} **{ev.get('event_type', '?')}** — {ev.get('created_at', '')[:19]}")
                    if ev.get("details"):
                        st.caption(str(ev["details"])[:200])
            else:
                st.info("No security events recorded")

    with tab4:
        st.subheader("Security Statistics")
        resp = requests.get(f"{API_URL}/nextgen/security/stats", headers=headers, timeout=5)
        if resp.ok:
            stats = resp.json()
            col1, col2 = st.columns(2)
            col1.metric("Total Events", stats.get("total_events", 0))
            by_sev = stats.get("by_severity", {})
            col2.metric("Critical", by_sev.get("CRITICAL", 0))
            col2.metric("Warnings", by_sev.get("WARN", 0))

# ============================================================
# OBSERVABILITY
# ============================================================
elif page == "📈 Observability":
    st.header("📈 Observability & Traces")

    tab1, tab2, tab3 = st.tabs(["📊 Metrics", "🔗 Traces", "🏥 System"])

    with tab1:
        st.subheader("Prometheus Metrics")
        try:
            resp = requests.get(f"{API_URL}/platform/metrics", headers=headers, timeout=5)
            if resp.ok:
                st.code(resp.text, language="text")
        except Exception:
            st.error("Metrics endpoint not reachable")

        st.subheader("JSON Metrics")
        resp = requests.get(f"{API_URL}/platform/metrics/json", headers=headers, timeout=5)
        if resp.ok:
            st.json(resp.json())

    with tab2:
        st.subheader("Analysis Traces")
        resp = requests.get(f"{API_URL}/nextgen/traces?limit=20", headers=headers, timeout=5)
        if resp.ok:
            traces = resp.json()
            if traces:
                for t in traces:
                    with st.expander(f"**{t.get('trace_id', '?')}** — {t.get('status', '?')} — {t.get('total_duration_ms', 0):.0f}ms"):
                        for span in t.get("spans", []):
                            icon = "✅" if span.get("status") == "OK" else "❌"
                            st.markdown(f"{icon} **{span.get('module', '?')}** — {span.get('duration_ms', 0):.0f}ms")
            else:
                st.info("No traces yet — run an analysis to generate traces")

        st.subheader("Trace Summary")
        resp = requests.get(f"{API_URL}/nextgen/traces/summary", headers=headers, timeout=5)
        if resp.ok:
            summary = resp.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Traces", summary.get("total_traces", 0))
            col2.metric("Completed", summary.get("completed", 0))
            col3.metric("Avg Duration", f"{summary.get('avg_duration_ms', 0):.0f}ms")

    with tab3:
        st.subheader("System Health")
        resp = requests.get(f"{API_URL}/nextgen/health/detailed", headers=headers, timeout=10)
        if resp.ok:
            health = resp.json()
            for comp in health.get("components", []):
                icon = {"HEALTHY": "🟢", "DEGRADED": "🟡", "UNAVAILABLE": "🔴"}.get(comp["status"], "⚪")
                st.markdown(f"{icon} **{comp['name']}** — {comp['detail']}")

# ============================================================
# RESEARCH
# ============================================================
elif page == "🔬 Research":
    st.header("🔬 Research Lab")

    tab1, tab2, tab3 = st.tabs(["🎯 Red Team", "📉 Drift", "🔄 Reproducibility"])

    with tab1:
        st.subheader("Red Team — Robustness Testing")
        st.caption("Test how detection holds up under transformations")
        red_file = st.file_uploader("Upload image for robustness test", type=["jpg", "jpeg", "png"], key="redteam")
        if red_file and st.button("Run Red Team Test"):
            with st.spinner("Running transformations..."):
                files = {"file": (red_file.name, red_file.getvalue(), red_file.type)}
                resp = requests.post(f"{API_URL}/nextgen/red-team/image", files=files, timeout=120)
                if resp.ok:
                    result = resp.json()
                    st.metric("Original Score", f"{result.get('original_score', 0):.0%}")
                    st.metric("Robustness Score", f"{result.get('robustness_score', 0):.0f}%")
                    st.metric("Worst Degradation", f"{result.get('worst_degradation', 0):.0%}")

                    # Transformation results
                    transforms = result.get("transformations", [])
                    if transforms:
                        df = pd.DataFrame([t for t in transforms if "name" in t])
                        if not df.empty:
                            fig = px.bar(df, x="name", y="diff", title="Score Change per Transformation",
                                        color="diff", color_continuous_scale="RdYlGn_r")
                            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "#f1f5f9"})
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Red team test failed — model may not be loaded")

    with tab2:
        st.subheader("Model Drift Detection")
        st.caption("Monitor if real-world inputs differ from training baseline")

        # Record observations
        with st.form("drift_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                confidence = st.slider("Confidence", 0.0, 1.0, 0.7)
            with col2:
                label = st.selectbox("Label", ["fake", "real"])
            with col3:
                modality = st.selectbox("Modality", ["text", "image", "video", "audio"])
            if st.form_submit_button("Record Observation"):
                requests.post(f"{API_URL}/nextgen/drift/observe", json={
                    "confidence": confidence, "label": label, "modality": modality,
                }, timeout=5)
                st.toast("Observation recorded!")

        # Detect drift
        if st.button("Run Drift Detection"):
            resp = requests.get(f"{API_URL}/nextgen/drift/detect", headers=headers, timeout=10)
            if resp.ok:
                result = resp.json()
                status = result.get("status", "NORMAL")
                icon = {"NORMAL": "🟢", "POSSIBLE_DRIFT": "🟡", "DRIFT_DETECTED": "🔴"}.get(status, "⚪")
                st.markdown(f"## {icon} Status: **{status}**")
                st.caption(f"Based on {result.get('observations_count', 0)} observations")

                alerts = result.get("alerts", [])
                if alerts:
                    for alert in alerts:
                        sev = alert.get("severity", "LOW")
                        st.warning(f"**{alert.get('metric', '?')}**: {alert.get('recommendation', '')}")

    with tab3:
        st.subheader("Analysis Reproducibility")
        st.caption("Check if a previous analysis can be reproduced")
        with st.form("reproduce_form"):
            orig_risk = st.number_input("Original risk score", 0, 100, 78)
            repro_risk = st.number_input("Reproduced risk score", 0, 100, 78)
            tolerance = st.slider("Tolerance (%)", 0.0, 10.0, 2.0)
            if st.form_submit_button("Check Reproducibility"):
                resp = requests.post(f"{API_URL}/nextgen/reproduce", json={
                    "original_signals": {"risk_score": orig_risk},
                    "reproduced_signals": {"risk_score": repro_risk},
                    "tolerance": tolerance,
                }, headers=headers, timeout=10)
                if resp.ok:
                    result = resp.json()
                    status = result.get("status", "?")
                    icon = {"REPRODUCIBLE": "✅", "RESULT_DIFFERENCE": "❌", "MODULE_DIFFERENCE": "⚠️"}.get(status, "❓")
                    st.markdown(f"### {icon} {status}")
                    st.caption(result.get("summary", ""))
                    st.metric("Risk Difference", f"{result.get('risk_difference', 0):.1f}%")

# ============================================================
# MODEL MANAGEMENT
# ============================================================
elif page == "🤖 Model Management":
    st.header("🤖 Model Management")

    tab1, tab2 = st.tabs(["⚖️ Champion vs Challenger", "📊 Benchmarks"])

    with tab1:
        st.subheader("Model Comparison")
        with st.form("comparison_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                modality = st.selectbox("Modality", ["image", "nlp", "video", "audio"])
            with col2:
                champion_ver = st.text_input("Champion Version", "1.0")
            with col3:
                challenger_ver = st.text_input("Challenger Version", "1.1")
            if st.form_submit_button("Run Comparison"):
                resp = requests.post(f"{API_URL}/nextgen/red-team/image" if modality == "image" else f"{API_URL}/predict/{modality}",
                    json={"text": "test comparison"}, headers=headers, timeout=10)
                # For now, simulate
                st.info("Comparison requires test dataset — use API endpoint directly")

        st.subheader("Previous Comparisons")
        st.info("Run comparisons to see results here")

    with tab2:
        st.subheader("Model Benchmarks")
        try:
            resp = requests.get(f"{API_URL}/performance", headers=headers, timeout=5)
            if resp.ok:
                st.json(resp.json())
        except Exception:
            st.info("Performance data not available")

# ============================================================
# PLATFORM
# ============================================================
elif page == "📱 Platform":
    st.header("📱 Platform Features")

    tab1, tab2, tab3, tab4 = st.tabs(["🔗 Webhooks", "📱 WhatsApp", "🌐 Social Monitor", "📋 GDPR"])

    with tab1:
        st.subheader("Webhook Integrations")
        with st.form("webhook_form"):
            wh_name = st.text_input("Name", "Slack Alerts")
            wh_url = st.text_input("Webhook URL", "https://hooks.slack.com/services/...")
            wh_platform = st.selectbox("Platform", ["slack", "discord", "pagerduty", "custom"])
            if st.form_submit_button("Register"):
                resp = requests.post(f"{API_URL}/platform/webhooks", json={
                    "name": wh_name, "url": wh_url, "platform": wh_platform,
                }, headers=headers, timeout=5)
                if resp.ok:
                    st.success(f"Webhook registered: {resp.json().get('id')}")

        resp = requests.get(f"{API_URL}/platform/webhooks", headers=headers, timeout=5)
        if resp.ok:
            whs = resp.json()
            if whs:
                for wh in whs:
                    st.markdown(f"**{wh['name']}** ({wh['platform']}) — {'✅' if wh['enabled'] else '❌'}")

        if st.button("Test Webhook"):
            resp = requests.post(f"{API_URL}/platform/webhooks/test", headers=headers, timeout=10)
            if resp.ok:
                st.json(resp.json())

    with tab2:
        st.subheader("WhatsApp Bot")
        st.markdown("""
        **Setup:**
        1. Get a WhatsApp Business API token from Meta
        2. Set env vars: `TL_WHATSAPP_TOKEN`, `TL_WHATSAPP_PHONE_ID`
        3. Configure webhook URL: `{API_URL}/platform/whatsapp/webhook`
        4. Run: `python -m backend.bots.whatsapp_bot`
        """)
        st.code(f"TL_WHATSAPP_TOKEN=your_token TL_WHATSAPP_PHONE_ID=your_id python -m backend.bots.whatsapp_bot")

    with tab3:
        st.subheader("Social Media Monitor")
        with st.form("monitor_form"):
            mon_url = st.text_input("URL to monitor", "https://twitter.com/user/status/123")
            mon_threshold = st.slider("Alert threshold", 0.0, 1.0, 0.7)
            if st.form_submit_button("Add to Monitor"):
                resp = requests.post(f"{API_URL}/platform/monitor", json={
                    "url": mon_url, "alert_threshold": mon_threshold,
                }, headers=headers, timeout=5)
                if resp.ok:
                    st.success("URL added to monitoring")

        resp = requests.get(f"{API_URL}/platform/monitor", headers=headers, timeout=5)
        if resp.ok:
            urls = resp.json()
            if urls:
                for u in urls:
                    st.markdown(f"**{u['url'][:60]}** — Last score: {u.get('last_threat_score', 'N/A')}")

        st.subheader("Active Alerts")
        resp = requests.get(f"{API_URL}/platform/alerts?limit=10", headers=headers, timeout=5)
        if resp.ok:
            alerts = resp.json()
            if alerts:
                for a in alerts:
                    sev = a.get("severity", "LOW")
                    icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}.get(sev, "⚪")
                    st.markdown(f"{icon} **{a.get('url', '?')[:50]}** — Score: {a.get('threat_score', 0):.0f}")

    with tab4:
        st.subheader("GDPR Compliance")
        with st.form("gdpr_form"):
            gdpr_type = st.selectbox("Request Type", ["access", "erasure", "portability", "rectification"])
            gdpr_subject = st.text_input("Subject ID")
            if st.form_submit_button("Submit Request"):
                resp = requests.post(f"{API_URL}/platform/gdpr/request", json={
                    "request_type": gdpr_type, "subject_id": gdpr_subject,
                }, headers=headers, timeout=5)
                if resp.ok:
                    st.success(f"Request submitted: {resp.json().get('id')}")

        resp = requests.get(f"{API_URL}/platform/gdpr/requests", headers=headers, timeout=5)
        if resp.ok:
            reqs = resp.json()
            if reqs:
                for r in reqs[-10:]:
                    st.markdown(f"**{r.get('request_type', '?')}** — {r.get('subject_id', '?')} — {r.get('status', '?')}")

# Footer
st.markdown("---")
st.caption(f"TruthLens Admin Dashboard — API: {API_URL} — v1.0.0")
