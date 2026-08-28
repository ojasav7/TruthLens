#!/usr/bin/env python3
"""TruthLens CLI — Command-line misinformation detection.

Usage:
    truthlens analyze "Breaking: aliens land in Times Square"
    truthlens analyze --file article.txt
    truthlens analyze --url https://example.com/article
    truthlens health
    truthlens history

Setup:
    export TRUTHLENS_API="http://localhost:8000"  # or your deployed URL
    pip install requests

Or install globally:
    pip install -e cli/
    truthlens analyze "test text"
"""

import sys
import os
import json
import argparse

API_URL = os.getenv("TRUTHLENS_API", "http://localhost:8000")


def analyze_text(text: str):
    """Analyze text for misinformation."""
    import requests
    try:
        r = requests.post(f"{API_URL}/analyze", data={"text": text}, timeout=30)
        r.raise_for_status()
        d = r.json()
        
        score = d["threat_score"]
        verdict = d["verdict"]
        
        # Color codes
        if verdict == "Low":
            color = "\033[92m"  # green
            icon = "[LOW]"
        elif verdict == "Review Needed":
            color = "\033[93m"  # yellow
            icon = "[REVIEW]"
        else:
            color = "\033[91m"  # red
            icon = "[HIGH]"
        
        reset = "\033[0m"
        
        print(f"\n{color}{icon} {verdict}{reset}")
        print(f"   Threat Score: {color}{score}/100{reset}")
        print(f"   Trace ID:     {d.get('trace_id', 'N/A')}")
        print()
        
        # Breakdown
        for mod, detail in d.get("breakdown", {}).items():
            if detail and isinstance(detail, dict) and "label" in detail:
                mod_color = "\033[91m" if detail["label"] in ("fake", "cloned") else "\033[92m"
                print(f"   {mod.upper():8s}: {mod_color}{detail['label']:8s}{reset} ({detail['confidence']*100:.1f}%)")
        
        print()
        
    except requests.exceptions.ConnectionError:
        print(f"\033[91mError: Cannot connect to {API_URL}\033[0m")
        print(f"Make sure TruthLens API is running: uvicorn backend.main:app --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\033[91mError: {e}\033[0m")
        sys.exit(1)


def analyze_file(filepath: str):
    """Analyze a text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        if len(text) > 10000:
            print(f"Warning: Truncating to 10,000 chars (was {len(text)})")
            text = text[:10000]
        analyze_text(text)
    except FileNotFoundError:
        print(f"\033[91mError: File not found: {filepath}\033[0m")
        sys.exit(1)


def health():
    """Check API health."""
    import requests
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        d = r.json()
        if d.get("status") == "healthy":
            print(f"[OK] TruthLens API is healthy")
        else:
            print(f"[WARN] API returned: {d}")
    except Exception:
        print(f"[FAIL] Cannot connect to {API_URL}")
        sys.exit(1)


def history(limit: int = 10):
    """Show recent analyses."""
    import requests
    try:
        r = requests.get(f"{API_URL}/analyses?limit={limit}", timeout=5)
        analyses = r.json()
        
        if not analyses:
            print("No analyses yet.")
            return
        
        print(f"\nRecent Analyses ({len(analyses)}):")
        print("-" * 60)
        for a in analyses:
            score = a.get("threat_score", 0)
            verdict = a.get("verdict", "?")
            ts = a.get("timestamp", "")[:19]
            print(f"  {ts}  {score:5.1f}/100  {verdict}")
        print()
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="TruthLens CLI — Detect misinformation from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  truthlens analyze "Breaking: aliens land in Times Square"
  truthlens analyze --file article.txt
  truthlens health
  truthlens history

Environment:
  TRUTHLENS_API  API URL (default: http://localhost:8000)
        """
    )
    
    sub = parser.add_subparsers(dest="command")
    
    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze text for misinformation")
    p_analyze.add_argument("text", nargs="?", help="Text to analyze")
    p_analyze.add_argument("--file", "-f", help="Read text from file")
    
    # health
    sub.add_parser("health", help="Check API health")
    
    # history
    p_history = sub.add_parser("history", help="Show recent analyses")
    p_history.add_argument("--limit", "-n", type=int, default=10, help="Number of results")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        if args.file:
            analyze_file(args.file)
        elif args.text:
            analyze_text(args.text)
        else:
            # Read from stdin
            text = sys.stdin.read().strip()
            if text:
                analyze_text(text)
            else:
                print("Provide text as argument, --file, or via stdin")
                sys.exit(1)
    elif args.command == "health":
        health()
    elif args.command == "history":
        history(args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
