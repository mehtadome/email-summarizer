"""
Email summarizer — entry point.

Usage:
  python -m scripts.main            # start Flask API (port 8000) + daily 5pm scheduler
  python -m scripts.main --now      # run a digest immediately and exit
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from scripts.fetcher import fetch_emails
from scripts.summarizer import summarize


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "summaries"))


def run_digest(hours_back: int = 24) -> Path:
    """Fetch emails, summarize, save JSON, return the output path."""
    print(f"[digest] Fetching emails from the last {hours_back} hours...")
    emails = fetch_emails(hours_back=hours_back)
    print(f"[digest] Found {len(emails)} email(s). Summarizing...")

    digest = summarize(emails, hours_back=hours_back)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_path = OUTPUT_DIR / f"{timestamp}.json"
    out_path.write_text(json.dumps(digest.model_dump(), indent=2, ensure_ascii=False))

    print(f"[digest] Saved → {out_path}")
    print(f"[digest] {digest.total_emails} emails | {digest.overall_summary[:120]}...")
    return out_path


def _scheduled_job():
    try:
        run_digest()
    except Exception as exc:
        print(f"[digest] ERROR: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Email summarizer")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run a digest immediately and exit instead of waiting for 5 PM.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many hours back to fetch emails (default: 24).",
    )
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.")

    if args.now:
        run_digest(hours_back=args.hours)
    else:
        from scripts.scheduler import start as start_scheduler
        from scripts.api import start as start_api

        scheduler = start_scheduler(_scheduled_job)

        try:
            start_api(host="127.0.0.1", port=8000)
        finally:
            scheduler.shutdown()


if __name__ == "__main__":
    main()
