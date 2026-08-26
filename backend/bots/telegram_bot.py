"""Telegram Bot — accepts text/images, runs TruthLens analysis, returns verdict.

Usage:
    Set TL_TELEGRAM_TOKEN env var, then:
    python -m backend.bots.telegram_bot

Requires: pip install python-telegram-bot
"""

import os
import io
import asyncio

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("Install python-telegram-bot: pip install python-telegram-bot")
    raise SystemExit(1)


# Lazy import — don't load models until bot starts
_app = None


def _get_app():
    global _app
    if _app is None:
        from backend.services.model_loader import load_all_models
        from backend.db.database import engine, Base
        from backend.db import models, models_advanced

        async def _init():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.get_event_loop().run_until_complete(_init())
        load_all_models()
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 TruthLens Bot\n\n"
        "Send me text or an image and I'll analyze it for misinformation.\n\n"
        "Commands:\n"
        "/start — This message\n"
        "/analyze — Analyze text (reply to a message)\n"
        "/help — Help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n"
        "• Send any text → I'll classify it as real/fake\n"
        "• Send an image → I'll check for deepfake indicators\n"
        "• Reply to a message with /analyze → I'll analyze the replied content"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or text.startswith("/"):
        return

    await update.message.reply_text("⏳ Analyzing...")

    try:
        from backend.services.model_loader import get_nlp_model
        model = get_nlp_model()
        if not model:
            await update.message.reply_text("⚠️ NLP model not loaded.")
            return

        result = model.predict(text)
        label_emoji = "🔴" if result["label"] == "fake" else "🟢"
        confidence = result["confidence"] * 100

        await update.message.reply_text(
            f"{label_emoji} **{result['label'].upper()}** ({confidence:.1f}% confidence)\n\n"
            f"Text: {text[:200]}{'...' if len(text) > 200 else ''}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Analyzing image...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()

        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        from backend.services.model_loader import get_image_model
        model = get_image_model()
        if not model:
            await update.message.reply_text("⚠️ Image model not loaded.")
            return

        result = model.predict(img)
        label_emoji = "🔴" if result["label"] == "fake" else "🟢"
        confidence = result["confidence"] * 100

        await update.message.reply_text(
            f"{label_emoji} **{result['label'].upper()}** ({confidence:.1f}% confidence)\n\n"
            f"Image analysis complete.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


def main():
    token = os.getenv("TL_TELEGRAM_TOKEN")
    if not token:
        print("Set TL_TELEGRAM_TOKEN env var first")
        return

    _get_app()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("analyze", handle_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 TruthLens Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
