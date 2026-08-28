"""TruthLens Email Plugin — Forward suspicious emails for analysis.

Usage:
    export TRUTHLENS_API="http://localhost:8000"
    python integrations/email_plugin/truthlens_email.py --email suspicious@email.com
    python integrations/email_plugin/truthlens_email.py --file email.eml
    echo "Check this news article" | python integrations/email_plugin/truthlens_email.py --stdin

Setup:
    pip install requests

How it works:
    1. Read email (from file, stdin, or IMAP)
    2. Extract text content
    3. Send to TruthLens API
    4. Return analysis result
"""

import os
import sys
import json
import argparse
import email
import imaplib
from email.header import decode_header

API_URL = os.getenv("TRUTHLENS_API", "http://localhost:8000")


def extract_text_from_eml(filepath: str) -> str:
    """Extract text content from .eml file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        msg = email.message_from_file(f)
    
    text_parts = []
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                text_parts.append(payload.decode(charset, errors="replace"))
    
    return "\n".join(text_parts)


def extract_text_from_imap(host: str, user: str, password: str, folder: str = "INBOX", limit: int = 5) -> list[dict]:
    """Fetch recent emails from IMAP server."""
    import imaplib
    
    mail = imaplib.IMAP4_SSL(host)
    mail.login(user, password)
    mail.select(folder)
    
    _, data = mail.search(None, "ALL")
    mail_ids = data[0].split()
    
    emails = []
    for mid in mail_ids[-limit:]:
        _, msg_data = mail.fetch(mid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        
        subject = msg["Subject"] or ""
        if subject:
            decoded = decode_header(subject)
            subject = "".join(
                part.decode(charset or "utf-8") if isinstance(part, bytes) else part
                for part, charset in decoded
            )
        
        # Extract body
        body = ""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
        
        emails.append({"subject": subject, "from": msg["From"], "body": body})
    
    mail.logout()
    return emails


def analyze_text(text: str) -> dict:
    """Send text to TruthLens API for analysis."""
    import requests
    try:
        r = requests.post(f"{API_URL}/analyze", data={"text": text}, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def print_result(result: dict, subject: str = ""):
    """Pretty-print analysis result."""
    if "error" in result:
        print(f"\033[91mError: {result['error']}\033[0m")
        return
    
    score = result["threat_score"]
    verdict = result["verdict"]
    
    if verdict == "Low":
        color = "\033[92m"
        icon = "🟢"
    elif verdict == "Review Needed":
        color = "\033[93m"
        icon = "🟡"
    else:
        color = "\033[91m"
        icon = "🔴"
    
    reset = "\033[0m"
    
    if subject:
        print(f"\n📧 {subject[:80]}")
    
    print(f"   {color}{icon} {verdict} — {score}/100{reset}")
    
    for mod, detail in result.get("breakdown", {}).items():
        if detail and isinstance(detail, dict) and "label" in detail:
            mod_icon = "🔴" if detail["label"] in ("fake", "cloned") else "🟢"
            print(f"   {mod.upper():8s}: {mod_icon} {detail['label']} ({detail['confidence']*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Analyze emails for misinformation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Analyze .eml file")
    group.add_argument("--stdin", action="store_true", help="Read from stdin")
    group.add_argument("--imap", nargs=3, metavar=("HOST", "USER", "PASS"), help="Fetch from IMAP")
    group.add_argument("--email", "-e", help="IMAP fetch (uses env IMAP_HOST)")
    
    parser.add_argument("--limit", "-n", type=int, default=5, help="Email limit for IMAP")
    parser.add_argument("--folder", default="INBOX", help="IMAP folder")
    
    args = parser.parse_args()
    
    if args.file:
        text = extract_text_from_eml(args.file)
        result = analyze_text(text)
        print_result(result, subject=os.path.basename(args.file))
    
    elif args.stdin:
        text = sys.stdin.read().strip()
        if not text:
            print("No text provided")
            sys.exit(1)
        result = analyze_text(text)
        print_result(result)
    
    elif args.imap:
        host, user, password = args.imap
        emails = extract_text_from_imap(host, user, password, args.folder, args.limit)
        for em in emails:
            combined = f"Subject: {em['subject']}\nFrom: {em['from']}\n\n{em['body']}"
            result = analyze_text(combined)
            print_result(result, subject=em["subject"])
    
    elif args.email:
        # Use IMAP with env vars
        host = os.getenv("IMAP_HOST", "imap.gmail.com")
        user = os.getenv("IMAP_USER", args.email)
        password = os.getenv("IMAP_PASS", "")
        if not password:
            print("Set IMAP_PASS env var")
            sys.exit(1)
        emails = extract_text_from_imap(host, user, password, args.folder, args.limit)
        for em in emails:
            combined = f"Subject: {em['subject']}\nFrom: {em['from']}\n\n{em['body']}"
            result = analyze_text(combined)
            print_result(result, subject=em["subject"])


if __name__ == "__main__":
    main()
