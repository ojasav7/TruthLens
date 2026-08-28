"""Feature Flags — central config for optional advanced modules."""

import os


def _flag(name: str, default: str = "true") -> bool:
    return os.getenv(f"TL_{name}", default).lower() == "true"


class FeatureFlags:
    # Stage A
    INVESTIGATION_MODE = _flag("INVESTIGATION_MODE")
    EVIDENCE_ENGINE = _flag("EVIDENCE_ENGINE")
    AUDIT_TRAIL = _flag("AUDIT_TRAIL")
    MODEL_VERSION_TRACKING = _flag("MODEL_VERSIONS")

    # Stage B
    CONTRADICTION_ENGINE = _flag("CONTRADICTION")
    VIDEO_TIMELINE = _flag("VIDEO_TIMELINE")
    EXPLANATION_ENGINE = _flag("EXPLANATION")

    # Stage C
    CASE_MANAGEMENT = _flag("CASE_MGMT")
    HUMAN_REVIEW = _flag("HUMAN_REVIEW")

    # Stage D
    SCREENSHOT_INVESTIGATION = _flag("SCREENSHOT")
    CLAIM_EXTRACTION = _flag("CLAIMS")

    # Stage E
    PERFORMANCE_MONITOR = _flag("PERF_MONITOR")

    # Existing stretch features
    OCR = _flag("OCR")
    EXIF = _flag("EXIF")
    CREDIBILITY = _flag("CREDIBILITY")

    # Next-gen: Reliability
    ENABLE_ENSEMBLE = _flag("ENSEMBLE")
    ENABLE_UNCERTAINTY = _flag("UNCERTAINTY")
    ENABLE_CONSISTENCY_CHECK = _flag("CONSISTENCY_CHECK")
    ENABLE_EVIDENCE_QUALITY = _flag("EVIDENCE_QUALITY")
    ENABLE_COUNTERFACTUALS = _flag("COUNTERFACTUALS")

    # Next-gen: Security
    ENABLE_SECURE_SANDBOX = _flag("SECURE_SANDBOX")
    ENABLE_PRIVACY_MODE = _flag("PRIVACY_MODE")
    ENABLE_DATA_RETENTION = _flag("DATA_RETENTION")

    # Next-gen: Performance
    ENABLE_SMART_CACHE = _flag("SMART_CACHE")
    ENABLE_SIMILARITY = _flag("SIMILARITY")
    ENABLE_ASYNC_ANALYSIS = _flag("ASYNC_ANALYSIS")

    # Next-gen: Research
    ENABLE_RED_TEAM = _flag("RED_TEAM")
    ENABLE_DRIFT_MONITORING = _flag("DRIFT_MONITORING")
    ENABLE_MODEL_CHALLENGER = _flag("MODEL_CHALLENGER")

    # Next-gen: Operations
    ENABLE_OBSERVABILITY = _flag("OBSERVABILITY")
    ENABLE_GOLDEN_TESTS = _flag("GOLDEN_TESTS")

    # Next-gen: Adaptive
    ENABLE_ADAPTIVE_ANALYSIS = _flag("ADAPTIVE_ANALYSIS", "false")

    # Investigation Intelligence
    ENABLE_EVIDENCE_CHAIN = _flag("EVIDENCE_CHAIN")
    ENABLE_REPRODUCIBILITY = _flag("REPRODUCIBILITY")
    ENABLE_CONFLICT_RESOLUTION = _flag("CONFLICT_RESOLUTION")
    ENABLE_ANNOTATIONS = _flag("ANNOTATIONS")
    ENABLE_INVESTIGATION_COPILOT = _flag("INVESTIGATION_COPILOT")
    ENABLE_INTEGRITY_SCORE = _flag("INTEGRITY_SCORE")
    ENABLE_INVESTIGATION_CONFIDENCE = _flag("INV_CONFIDENCE")


flags = FeatureFlags()
