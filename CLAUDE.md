# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Email summarizer — fetches emails and produces AI-generated summaries using the Claude API.

## Environment

Python project using a `.venv` virtual environment.

```bash
source .venv/bin/activate   # activate
pip install -r requirements.txt  # install deps
```

## Running

```bash
# Start Flask API (port 8000) + daily 5pm scheduler — normal mode
python -m scripts.main

# Run a digest right now and exit (good for testing)
python -m scripts.main --now

# Fetch the last 72 hours instead of 24
python -m scripts.main --now --hours 72
```

In a second terminal, start the frontend dev server:

```bash
cd frontend && npm install && npm run dev
# → http://localhost:5173  (Vite proxies /api → localhost:8000)
```

First run will open a browser for Gmail OAuth. The token is saved to `token.json`.

### Setup checklist

1. Copy `.env.example` → `.env` and add `ANTHROPIC_API_KEY`
2. Download `credentials.json` from Google Cloud Console (Gmail API, OAuth 2.0 Desktop client)
3. Place `credentials.json` in the project root
4. `pip install -r requirements.txt`

## Architecture

```
scripts/
  fetcher.py     — Gmail OAuth2 auth + email fetch (last N hours)
  summarizer.py  — Claude API call; returns structured Digest (Pydantic model)
  scheduler.py   — APScheduler background scheduler, fires at 17:00 daily
  api.py         — FastAPI server (port 8000); routes listed below
  main.py        — CLI entry point; starts Flask + scheduler together

frontend/        — React + TypeScript + Vite (proxies /api → :8000)
summaries/       — output JSON files, one per run (YYYY-MM-DD_HH-MM.json)
credentials.json — Gmail OAuth2 client secrets (not committed)
token.json       — stored OAuth token after first login (not committed)
```

### API routes (Flask, port 8000)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sample-text` | Overall summary from latest digest (used by frontend on load) |
| GET | `/api/digests` | List all digests (metadata only), newest first |
| GET | `/api/digests/latest` | Full latest digest JSON |
| GET | `/api/digests/<filename>` | Specific digest by filename |
| POST | `/api/run` | Trigger a digest run in the background |

### Design decisions

- **Provider**: Gmail first (OAuth2 via google-auth-oauthlib). Outlook support is in `todo.md`.
- **Schedule**: Daily at 17:00 local time (override with `TIMEZONE=America/New_York` in `.env`).
- **Importance algorithm**: Claude determines high/medium/low based on content — no sender whitelisting.
- **Output format**: JSON saved to `summaries/`. Each file is a `Digest` with per-email entries and an overall summary.
- **Prompt caching**: System prompt is cached (`cache_control: ephemeral`) to reduce API costs on repeated runs.
