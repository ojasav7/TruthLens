"""Social Media URL Intelligence — analyze shared links for credibility, bot signals, and manipulation.

Extends the existing credibility_service with social-media-specific analysis:
- Platform detection (Twitter/X, Facebook, Reddit, etc.)
- URL shortener detection
- Redirect chain analysis
- Engagement manipulation signals
"""

import re
from urllib.parse import urlparse, parse_qs

# Social media platforms and their URL patterns
SOCIAL_PLATFORMS = {
    "twitter.com": "Twitter/X",
    "x.com": "Twitter/X",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "instagram.com": "Instagram",
    "reddit.com": "Reddit",
    "linkedin.com": "LinkedIn",
    "tiktok.com": "TikTok",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "threads.net": "Threads",
    "mastodon.social": "Mastodon",
    "bsky.app": "Bluesky",
    "truthsocial.com": "Truth Social",
    "rumble.com": "Rumble",
    "t.me": "Telegram",
    "wa.me": "WhatsApp",
}

# Known URL shorteners
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bl.ink", "lnkd.in", "rb.gy", "cutt.ly",
    "shorturl.at", "tiny.cc", "clk.sh", "surl.li",
}

# Bot / manipulation signals in URLs
BOT_SIGNALS = [
    (r"\/\d{10,}\/?", "Numeric post ID (possible bot farm)"),
    (r"ref=[\w]+", "Referral tracking parameter"),
    (r"utm_", "UTM campaign tracking"),
    (r"fbclid=", "Facebook click ID"),
    (r"gclid=", "Google click ID"),
    (r"sa=[\w]+", "Social algorithm parameter"),
]


def analyze_url(url: str) -> dict:
    """
    Comprehensive URL analysis for social media intelligence.

    Returns:
        {
            "url": str,
            "domain": str,
            "platform": str | None,
            "is_shortened": bool,
            "shortener": str | None,
            "bot_signals": list[str],
            "credibility": str,
            "risk_score": float,
            "signals": list[str],
            "explanation": str,
        }
    """
    if not url or not isinstance(url, str):
        return {"error": "No URL provided"}

    # Normalize
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().removeprefix("www.")
    except Exception:
        return {"error": "Cannot parse URL"}

    signals = []
    bot_signals_found = []

    # --- Platform detection ---
    platform = None
    for plat_domain, plat_name in SOCIAL_PLATFORMS.items():
        if domain == plat_domain or domain.endswith("." + plat_domain):
            platform = plat_name
            break

    if platform:
        signals.append(f"Shared on {platform}")

    # --- Shortener detection ---
    is_shortened = domain in SHORTENERS
    shortener = domain if is_shortened else None
    if is_shortened:
        signals.append(f"URL shortened via {domain} — destination unknown")

    # --- Bot signals ---
    for pattern, description in BOT_SIGNALS:
        if re.search(pattern, url):
            bot_signals_found.append(description)
            signals.append(f"Bot signal: {description}")

    # --- Engagement manipulation detection ---
    # Check for suspicious query parameters
    params = parse_qs(parsed.query)
    suspicious_params = [k for k in params if k.startswith(("fb_", "tw_", "ref", "source"))]
    if suspicious_params:
        signals.append(f"Social tracking params: {', '.join(suspicious_params[:3])}")

    # --- Credibility assessment ---
    from backend.services.credibility_service import check_url
    cred_result = check_url(url)

    # Adjust risk based on signals
    risk = cred_result.get("risk_score", 0.5)
    if is_shortened:
        risk = min(1.0, risk + 0.1)
    if len(bot_signals_found) >= 2:
        risk = min(1.0, risk + 0.15)
    if platform in ("Truth Social", "Rumble"):
        risk = min(1.0, risk + 0.05)
    if platform in ("Reuters (via URL)", ) or cred_result.get("credibility") == "high":
        risk = max(0.0, risk - 0.2)

    credibility = "low" if risk >= 0.7 else "high" if risk <= 0.3 else "unknown"

    # --- Explanation ---
    parts = []
    if platform:
        parts.append(f"Detected on {platform}")
    if is_shortened:
        parts.append(f"Shortened via {domain}")
    if bot_signals_found:
        parts.append(f"{len(bot_signals_found)} bot signal(s) detected")
    if not parts:
        parts.append("No significant signals detected")

    return {
        "url": url,
        "domain": domain,
        "platform": platform,
        "is_shortened": is_shortened,
        "shortener": shortener,
        "bot_signals": bot_signals_found,
        "credibility": credibility,
        "risk_score": round(risk, 3),
        "signals": signals,
        "explanation": ". ".join(parts),
    }


def batch_analyze_urls(urls: list[str]) -> list[dict]:
    """Analyze multiple URLs and return results."""
    return [analyze_url(url) for url in urls]
