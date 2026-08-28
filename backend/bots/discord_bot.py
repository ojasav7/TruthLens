"""Discord Bot — TruthLens analysis in Discord servers.

Usage:
    export DISCORD_TOKEN="your-bot-token"
    python -m backend.bots.discord_bot

Setup:
    1. Go to https://discord.com/developers/applications → New Application
    2. Go to Bot → Add Bot → Copy Token
    3. Enable: MESSAGE CONTENT INTENT, SERVER MEMBERS INTENT
    4. Go to OAuth2 → URL Generator → Scopes: bot
    5. Bot Permissions: Send Messages, Read Message History, Attach Files
    6. Copy invite URL → add to server
"""

import os
import io
import logging

logger = logging.getLogger("truthlens.discord")


def main():
    try:
        import discord
        from discord.ext import commands
    except ImportError:
        print("Install discord.py: pip install discord.py")
        raise SystemExit(1)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Set DISCORD_TOKEN env var first")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"TruthLens bot logged in as {bot.user}")

    @bot.command(name="analyze")
    async def analyze(ctx, *, text: str = None):
        """Analyze text for misinformation: !analyze <text>"""
        if not text:
            await ctx.send("Usage: `!analyze <text to check>`")
            return

        async with ctx.typing():
            try:
                from backend.services.model_loader import get_nlp_model
                model = get_nlp_model()
                if not model:
                    await ctx.send("NLP model not loaded")
                    return

                result = model.predict(text)
                emoji = "🔴" if result["label"] == "fake" else "🟢"
                conf = result["confidence"] * 100

                embed = discord.Embed(
                    title=f"{emoji} {result['label'].upper()}",
                    description=f"**Confidence:** {conf:.1f}%\n**Text:** {text[:500]}",
                    color=discord.Color.red() if result["label"] == "fake" else discord.Color.green(),
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Error: {e}")

    @bot.command(name="factcheck")
    async def factcheck(ctx, *, claim: str = None):
        """Fact-check a claim: !factcheck <claim>"""
        if not claim:
            await ctx.send("Usage: `!factcheck <claim to verify>`")
            return

        async with ctx.typing():
            try:
                from backend.services.model_loader import get_nlp_model
                model = get_nlp_model()
                if model:
                    result = model.predict(claim)
                    emoji = "🔴" if result["label"] == "fake" else "🟢"
                    embed = discord.Embed(
                        title=f"{emoji} Fact-Check Result",
                        description=f"**{result['label'].upper()}** ({result['confidence']*100:.1f}%)\n> {claim[:500]}",
                        color=discord.Color.red() if result["label"] == "fake" else discord.Color.green(),
                    )
                    await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Error: {e}")

    @bot.command(name="health")
    async def health(ctx):
        """Check TruthLens API health"""
        import requests
        try:
            r = requests.get("http://localhost:8000/health", timeout=5)
            if r.ok:
                await ctx.send("TruthLens API: Healthy")
            else:
                await ctx.send("TruthLens API: Unhealthy")
        except:
            await ctx.send("TruthLens API: Unreachable")

    bot.run(token)


if __name__ == "__main__":
    main()
