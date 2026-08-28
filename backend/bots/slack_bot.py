"""Slack Bot — TruthLens analysis in Slack channels.

Usage:
    export SLACK_BOT_TOKEN="xoxb-your-token"
    export SLACK_SIGNING_SECRET="your-signing-secret"
    python -m backend.bots.slack_bot

Setup:
    1. Go to https://api.slack.com/apps → Create New App
    2. Enable Event Subscriptions → Request URL: https://your-server/slack/events
    3. Subscribe to: message.channels, message.im
    4. Add Bot Scopes: chat:write, files:read, files:write
    5. Install to workspace → copy Bot Token + Signing Secret
"""

import os
import io
import json
import logging

logger = logging.getLogger("truthlens.slack")

# Lazy imports
_app = None


def _get_app():
    global _app
    if _app is not None:
        return _app

    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
    except ImportError:
        print("Install slack-bolt: pip install slack-bolt")
        raise SystemExit(1)

    token = os.getenv("SLACK_BOT_TOKEN")
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")

    if not token:
        print("Set SLACK_BOT_TOKEN env var first")
        raise SystemExit(1)

    app = App(token=token, signing_secret=signing_secret or "")

    # --- Handlers ---

    @app.message("analyze")
    def handle_analyze(message, say):
        text = message.get("text", "").replace("analyze", "", 1).strip()
        if not text:
            say("Usage: `analyze <text to check>` or attach an image")
            return

        say("Analyzing...")
        try:
            from backend.services.model_loader import get_nlp_model
            model = get_nlp_model()
            if not model:
                say("NLP model not loaded")
                return

            result = model.predict(text)
            emoji = "🔴" if result["label"] == "fake" else "🟢"
            conf = result["confidence"] * 100

            say({
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *{result['label'].upper()}* ({conf:.1f}% confidence)\n>{text[:200]}"
                        }
                    }
                ]
            })
        except Exception as e:
            say(f"Error: {e}")

    @app.message("factcheck")
    def handle_factcheck(message, say):
        text = message.get("text", "").replace("factcheck", "", 1).strip()
        if not text:
            say("Usage: `factcheck <claim to verify>`")
            return

        say("Fact-checking...")
        try:
            from backend.services.model_loader import get_nlp_model
            model = get_nlp_model()
            if model:
                result = model.predict(text)
                emoji = "🔴" if result["label"] == "fake" else "🟢"
                say(f"{emoji} *Fact-check:* {result['label'].upper()} ({result['confidence']*100:.1f}%)")
            else:
                say("Model not available")
        except Exception as e:
            say(f"Error: {e}")

    @app.event("app_mention")
    def handle_mention(event, say):
        text = event.get("text", "")
        # Remove bot mention
        if "<@" in text:
            text = text.split(">", 2)[-1].strip() if text.count("<@") else text

        if not text:
            say("Mention me with: `analyze <text>` or `factcheck <claim>`")
            return

        say("Analyzing...")
        try:
            from backend.services.model_loader import get_nlp_model
            model = get_nlp_model()
            if model:
                result = model.predict(text)
                emoji = "🔴" if result["label"] == "fake" else "🟢"
                say(f"{emoji} *{result['label'].upper()}* ({result['confidence']*100:.1f}%)")
        except Exception as e:
            say(f"Error: {e}")

    _app = app
    return app


def main():
    logging.basicConfig(level=logging.INFO)

    app = _get_app()

    # Try Socket Mode first (no public URL needed)
    socket_token = os.getenv("SLACK_APP_TOKEN")
    if socket_token:
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        handler = SocketModeHandler(app, socket_token)
        print("Slack bot started (Socket Mode)")
        handler.start()
    else:
        print("Slack bot started (HTTP mode)")
        app.start(port=int(os.getenv("SLACK_PORT", "3000")))


if __name__ == "__main__":
    main()
