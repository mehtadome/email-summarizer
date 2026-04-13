> **Work in progress** — core plumbing is wired up; Gmail integration and the full digest UI are actively being built.

# Email Summarizer

A personal web app for staying on top of your inbox without living in it. The goal is a rich UI — not a terminal printout — where you can browse detailed email digests, see importance scores at a glance, and catch anything that matters before clocking out at 5 PM.

Built as a learning project to explore agentic AI in a practical context. The current version is a working skeleton; the plan is to evolve it toward richer per-email detail, user feedback on importance scores, and eventually push notifications for high-priority emails.

## How it works

1. **Fetch** — `backend/fetcher.py` authenticates with Gmail via OAuth2 and pulls emails from the last N hours.
2. **Summarize** — `backend/summarizer.py` sends them to Claude via the `claude-agent-sdk`, which routes through your local Claude Pro session (no separate API key needed). Claude assigns each email an importance level (high / medium / low) based on content — no sender whitelisting.
3. **Schedule** — `backend/scheduler.py` fires the job daily at 17:00 using APScheduler.
4. **Serve** — `backend/api.py` exposes a FastAPI server on port 8000 so the frontend can fetch digests and trigger runs on demand.
5. **Display** — a React + TypeScript + Vite frontend at `frontend/` shows the latest digest and lets you browse history.

## Current state

The frontend and backend are connected end-to-end. Clicking "Fetch digest info from backend" POSTs to the FastAPI server and displays the response in the dark-themed React UI.

Next milestone: wire up real Gmail credentials so the digest pipeline runs against a live inbox.

## Stack

| Layer | Tech |
|---|---|
| LLM | Anthropic Claude (`claude-opus-4-6`) |
| Backend | Python · FastAPI · APScheduler |
| Gmail auth | `google-auth-oauthlib` · OAuth2 |
| Frontend | React · TypeScript · Vite |

## Getting started

### Prerequisites

- Python 3.11+
- Node 18+
- Claude Code CLI with an active Pro subscription
- A Google Cloud project with the Gmail API enabled (see below)

### Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/mehtadome/email-summarizer
cd email-summarizer

# 2. Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Frontend dependencies
cd frontend && npm install && cd ..

# 4. Gmail credentials
# Download credentials.json from Google Cloud Console
# (APIs & Services → Credentials → OAuth 2.0 Desktop client)
# Place it in the project root — it is gitignored
```

### Run

```bash
make dev
```

This starts the FastAPI backend (`:8000`) and the Vite frontend (`:5173`) together. Ctrl+C stops both.

Open [http://localhost:5173](http://localhost:5173).

On first run, a browser window will open for Gmail OAuth consent. The resulting token is saved to `token.json` (gitignored).

To run a digest immediately without waiting for 5 PM:

```bash
python -m backend.main --now
# or fetch the last 72 hours:
python -m backend.main --now --hours 72
```

### Gmail API setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** under APIs & Services → Library.
3. Create an **OAuth 2.0 Client ID** (Application type: Desktop app).
4. Download the JSON file and save it as `credentials.json` in the project root.
5. Run the app — it will open a browser for the consent screen and save `token.json`.

## Roadmap

See [todo.md](todo.md) for the full task list. Up next:

- Digest browser UI (list + detail view for past digests)
- Configurable look-back window (e.g. 72-hour weekend catch-up)
- Importance feedback (thumbs up/down to evolve the algorithm)
- Push notifications for high-importance emails
