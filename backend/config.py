"""Feature Flags — central config for optional advanced modules."""

import os


class FeatureFlags:
    # Stage A
    INVESTIGATION_MODE = os.getenv("TL_INVESTIGATION_MODE", "true").lower() == "true"
    EVIDENCE_ENGINE = os.getenv("TL_EVIDENCE_ENGINE", "true").lower() == "true"
    AUDIT_TRAIL = os.getenv("TL_AUDIT_TRAIL", "true").lower() == "true"
    MODEL_VERSION_TRACKING = os.getenv("TL_MODEL_VERSIONS", "true").lower() == "true"

    # Stage B
    CONTRADICTION_ENGINE = os.getenv("TL_CONTRADICTION", "true").lower() == "true"
    VIDEO_TIMELINE = os.getenv("TL_VIDEO_TIMELINE", "true").lower() == "true"
    EXPLANATION_ENGINE = os.getenv("TL_EXPLANATION", "true").lower() == "true"

    # Stage C
    CASE_MANAGEMENT = os.getenv("TL_CASE_MGMT", "true").lower() == "true"
    HUMAN_REVIEW = os.getenv("TL_HUMAN_REVIEW", "true").lower() == "true"

    # Stage D
    SCREENSHOT_INVESTIGATION = os.getenv("TL_SCREENSHOT", "true").lower() == "true"
    CLAIM_EXTRACTION = os.getenv("TL_CLAIMS", "true").lower() == "true"

    # Stage E
    PERFORMANCE_MONITOR = os.getenv("TL_PERF_MONITOR", "true").lower() == "true"

    # Existing stretch features
    OCR = os.getenv("TL_OCR", "true").lower() == "true"
    EXIF = os.getenv("TL_EXIF", "true").lower() == "true"
    CREDIBILITY = os.getenv("TL_CREDIBILITY", "true").lower() == "true"


flags = FeatureFlags()
