"""Gap-Fill Router — Auth, Webhooks, Social Monitor, GDPR, Metrics, Forensics."""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/platform", tags=["Platform Features"])


# ============================================================
#  AUTH — Login / Register / Token
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"


@router.post("/auth/login")
async def login(body: LoginRequest):
    from backend.services.auth_service import authenticate_user
    token = authenticate_user(body.username, body.password)
    if not token:
        raise HTTPException(401, "Invalid credentials")
    return {"token": token, "token_type": "bearer"}


@router.post("/auth/register")
async def register(body: RegisterRequest):
    from backend.services.auth_service import register_user
    result = register_user(body.username, body.password, body.role)
    if not result:
        raise HTTPException(409, "User already exists")
    return result


@router.get("/auth/me")
async def auth_me(request: Request):
    from backend.services.auth_service import extract_user_from_request
    user = extract_user_from_request(request)
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, **user.to_dict()}


# ============================================================
#  WEBHOOKS — Slack, Discord, PagerDuty
# ============================================================

class WebhookRegisterRequest(BaseModel):
    name: str
    url: str
    platform: str
    events: list[str] | None = None


@router.post("/webhooks")
async def register_webhook(body: WebhookRegisterRequest):
    from backend.services.webhook_integrations import register_webhook
    return register_webhook(body.name, body.url, body.platform, body.events)


@router.get("/webhooks")
async def list_webhooks():
    from backend.services.webhook_integrations import list_webhooks
    return list_webhooks()


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    from backend.services.webhook_integrations import remove_webhook
    if not remove_webhook(webhook_id):
        raise HTTPException(404, "Webhook not found")
    return {"status": "deleted"}


@router.post("/webhooks/test")
async def test_webhook():
    from backend.services.webhook_integrations import dispatch_webhook
    return dispatch_webhook("alert", {"verdict": "High Risk", "threat_score": 85, "message": "Test alert from TruthLens"})


# ============================================================
#  SOCIAL MONITOR
# ============================================================

class MonitorRequest(BaseModel):
    url: str
    check_interval: int = 3600
    alert_threshold: float = 0.7
    platforms: list[str] | None = None


@router.post("/monitor")
async def add_to_monitor(body: MonitorRequest):
    from backend.services.social_monitor import add_url_to_monitor
    return add_url_to_monitor(body.model_dump())


@router.get("/monitor")
async def list_monitored():
    from backend.services.social_monitor import list_monitored_urls
    return list_monitored_urls()


@router.get("/alerts")
async def get_alerts(acknowledged: bool | None = None, limit: int = Query(50, le=200)):
    from backend.services.social_monitor import get_alerts
    return get_alerts(acknowledged=acknowledged, limit=limit)


@router.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: str):
    from backend.services.social_monitor import acknowledge_alert
    if not acknowledge_alert(alert_id):
        raise HTTPException(404, "Alert not found")
    return {"status": "acknowledged"}


@router.get("/monitor/detect-platform")
async def detect_platform(url: str = Query(...)):
    from backend.services.social_monitor import detect_platform
    return {"url": url, "platforms": detect_platform(url)}


# ============================================================
#  GDPR
# ============================================================

class GDPRRequestRequest(BaseModel):
    request_type: str
    subject_id: str
    details: dict | None = None


class ConsentRequest(BaseModel):
    subject_id: str
    purpose: str
    granted: bool


@router.post("/gdpr/request")
async def gdpr_request(body: GDPRRequestRequest):
    from backend.services.gdpr_service import submit_data_request
    return submit_data_request(body.request_type, body.subject_id, body.details)


@router.get("/gdpr/requests")
async def gdpr_requests(subject_id: str | None = None):
    from backend.services.gdpr_service import get_data_requests
    return get_data_requests(subject_id)


@router.get("/gdpr/processing-records")
async def processing_records():
    from backend.services.gdpr_service import get_processing_records
    return get_processing_records()


@router.post("/gdpr/consent")
async def record_consent(body: ConsentRequest):
    from backend.services.gdpr_service import record_consent
    return record_consent(body.subject_id, body.purpose, body.granted)


# ============================================================
#  PROMETHEUS METRICS
# ============================================================

@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    from backend.services.prometheus_metrics import render_prometheus_metrics
    return render_prometheus_metrics()


@router.get("/metrics/json")
async def metrics_json():
    from backend.services.prometheus_metrics import _requests_total, _errors_total, _analyses_total, _model_loaded, _active_jobs, START_TIME
    import time
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "requests_total": dict(_requests_total),
        "errors_total": dict(_errors_total),
        "analyses_total": dict(_analyses_total),
        "models_loaded": dict(_model_loaded),
        "active_jobs": _active_jobs,
    }


# ============================================================
#  FORENSIC REPORTS
# ============================================================

class ForensicReportRequest(BaseModel):
    analysis: dict
    evidence: list[dict] | None = None
    timeline: list[dict] | None = None
    model_versions: dict | None = None
    chain_of_custody: list[dict] | None = None


@router.post("/forensic-report")
async def generate_forensic_report(body: ForensicReportRequest):
    from backend.services.forensic_report import generate_forensic_report
    return generate_forensic_report(**body.model_dump())


@router.post("/webhook/dispatch")
async def dispatch_webhook_event(event_type: str = "alert"):
    from backend.services.webhook_integrations import dispatch_webhook
    return dispatch_webhook(event_type, {"verdict": "High Risk", "threat_score": 85, "message": f"TruthLens {event_type}"})


# ============================================================
#  WHATSAPP WEBHOOK
# ============================================================

@router.get("/whatsapp/webhook")
async def whatsapp_verify(mode: str = "", token: str = "", challenge: str = ""):
    from backend.bots.whatsapp_bot import verify_webhook
    result = verify_webhook(mode, token, challenge)
    if result:
        return PlainTextResponse(result)
    raise HTTPException(403, "Verification failed")


from fastapi.responses import JSONResponse as _JSONResponse

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    from backend.bots.whatsapp_bot import handle_webhook
    body = await request.json()
    return _JSONResponse(handle_webhook(body))


# ============================================================
#  ON-PREMISE / DEPLOYMENT INFO
# ============================================================

@router.get("/deployment/info")
async def deployment_info():
    import os
    return {
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "sqlite" if "sqlite" in os.getenv("DATABASE_URL", "sqlite") else "postgresql",
        "models": {
            "nlp": os.path.isdir(os.getenv("MODEL_DIR", "./models") + "/nlp/weights"),
            "image": os.path.isdir(os.getenv("MODEL_DIR", "./models") + "/image/weights"),
            "video": os.path.isdir(os.getenv("MODEL_DIR", "./models") + "/video/weights"),
            "audio": os.path.isdir(os.getenv("MODEL_DIR", "./models") + "/audio/weights"),
        },
        "features": {
            "jwt_auth": True,
            "rbac": True,
            "rate_limiting": True,
            "forensic_reports": True,
            "social_monitoring": True,
            "gdpr_compliance": True,
            "prometheus_metrics": True,
            "webhook_integrations": True,
            "whatsapp_bot": True,
            "browser_extension": True,
        },
        "deployment_options": {
            "docker": "docker-compose up --build",
            "kubernetes": "kubectl apply -f deploy/k8s/deployment.yaml",
            "on_premise": "See docs/ON_PREMISE.md",
        },
    }
