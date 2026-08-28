"""WhatsApp Bot — accepts text/images, runs TruthLens analysis, returns verdict.

Usage:
    Set TL_WHATSAPP_TOKEN and TL_WHATSAPP_PHONE_ID env vars, then:
    python -m backend.bots.whatsapp_bot

Requires: pip install requests
"""

import os
import io
import json
import logging
import hashlib
import requests as req

logger = logging.getLogger("truthlens.whatsapp")

API_URL = os.getenv("API_URL", "http://localhost:8000")
WHATSAPP_TOKEN = os.getenv("TL_WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("TL_WHATSAPP_PHONE_ID", "")
WEBHOOK_SECRET = os.getenv("TL_WHATSAPP_WEBHOOK_SECRET", "")


def send_whatsapp_message(to: str, text: str):
    """Send a text message via WhatsApp Business API."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        logger.warning("WhatsApp credentials not configured")
        return
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        resp = req.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error("WhatsApp send failed: %s", e)


def send_whatsapp_image(to: str, image_url: str, caption: str = ""):
    """Send an image via WhatsApp Business API."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption} if caption else {"link": image_url},
    }
    try:
        req.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        logger.error("WhatsApp image send failed: %s", e)


def handle_incoming_message(sender: str, message_type: str, content: str, media_url: str | None = None):
    """Process an incoming WhatsApp message through TruthLens."""
    if message_type == "text":
        if content.strip().lower() in ("help", "/help", "hi", "hello"):
            send_whatsapp_message(sender,
                "🔍 *TruthLens WhatsApp Bot*\n\n"
                "Send me any text, image, or video and I'll analyze it for misinformation.\n\n"
                "Commands:\n"
                "• Send text → Text analysis\n"
                "• Send image → Image deepfake check\n"
                "• Send video → Video analysis\n"
                "• /help → Show this message\n"
            )
            return

        # Analyze text
        try:
            resp = req.post(f"{API_URL}/predict/text", json={"text": content}, timeout=30)
            if resp.ok:
                result = resp.json()
                label = result.get("label", "unknown")
                conf = result.get("confidence", 0)
                icon = "🔴" if label == "fake" else "🟢" if label == "real" else "🟡"
                send_whatsapp_message(sender,
                    f"{icon} *Analysis Result*\n\n"
                    f"Label: *{label.upper()}*\n"
                    f"Confidence: {conf:.0%}\n\n"
                    f"_Powered by TruthLens AI_"
                )
            else:
                send_whatsapp_message(sender, "⚠️ Analysis failed. Please try again.")
        except Exception as e:
            send_whatsapp_message(sender, f"⚠️ Error: {str(e)[:100]}")

    elif message_type == "image" and media_url:
        try:
            # Download and analyze image
            img_resp = req.get(media_url, timeout=30)
            files = {"file": ("image.jpg", img_resp.content, "image/jpeg")}
            resp = req.post(f"{API_URL}/predict/image", files=files, timeout=30)
            if resp.ok:
                result = resp.json()
                label = result.get("label", "unknown")
                conf = result.get("confidence", 0)
                icon = "🔴" if label == "fake" else "🟢"
                send_whatsapp_message(sender,
                    f"{icon} *Image Analysis*\n\n"
                    f"Label: *{label.upper()}*\n"
                    f"Confidence: {conf:.0%}\n\n"
                    f"_Powered by TruthLens AI_"
                )
        except Exception as e:
            send_whatsapp_message(sender, f"⚠️ Image analysis error: {str(e)[:100]}")

    else:
        send_whatsapp_message(sender, "📤 Supported: text and images. Send /help for usage.")


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """Verify WhatsApp webhook subscription."""
    if mode == "subscribe" and token == WEBHOOK_SECRET:
        return challenge
    return None


def handle_webhook(payload: dict) -> dict:
    """Handle incoming WhatsApp webhook payload."""
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for msg in messages:
            sender = msg.get("from", "")
            msg_type = msg.get("type", "")

            if msg_type == "text":
                handle_incoming_message(sender, "text", msg.get("text", {}).get("body", ""))
            elif msg_type == "image":
                handle_incoming_message(sender, "image", "", msg.get("image", {}).get("id"))
            elif msg_type == "video":
                handle_incoming_message(sender, "video", "", msg.get("video", {}).get("id"))
            else:
                send_whatsapp_message(sender, "📤 Unsupported type. Send text or images.")

        return {"status": "ok"}
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return {"status": "error", "detail": str(e)}
