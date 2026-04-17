# Email Summarizer

A personal web app for staying on top of your inbox without living in it. Browse daily email digests with importance scores at a glance, catch anything that matters, and trigger a fresh run whenever you want.

Built as a learning project to explore agentic AI in a practical context.

## How it works

1. **Fetch** — `backend/fetcher.py` authenticates with Gmail via OAuth2 and pulls emails since the last digest run (falls back to 7 days on first run). Multiple accounts are supported via `GMAIL_ACCOUNTS`.
2. **Summarize** — `backend/summarizer.py` sends emails to the `claude` CLI, which routes through your local Claude Pro session (no separate API key needed). Claude assigns each email an importance level (high / medium / low) and writes a short summary.
3. **Serve** — `backend/api.py` exposes a FastAPI server on port 8000 so the frontend can fetch digests and trigger runs on demand.
4. **Display** — a React + TypeScript + Vite frontend at `frontend/` shows the latest digest headline + recommendations and lets you browse history by date.

## Stack

| Layer | Tech |
|---|---|
| LLM | Anthropic Claude (via `claude` CLI, local Pro session) |
| Backend | Python · FastAPI · APScheduler |
| Gmail auth | `google-auth-oauthlib` · OAuth2 |
| Frontend | React · TypeScript · Vite |

## Getting started

### Prerequisites

- Python 3.11+
- Node 18+
- Claude Code CLI with an active Pro subscription (`claude` must be on your PATH)
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

# 4. Environment
cp .env.example .env
# Edit .env:
#   GMAIL_ACCOUNTS=you@gmail.com,other@gmail.com   (at least one required)
#   TIMEZONE=America/New_York                        (optional, defaults to America/Los_Angeles)
#   ANTHROPIC_API_KEY is not needed — the claude CLI uses your Pro session

# 5. Gmail credentials
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

On first run, a browser window will open for Gmail OAuth consent per account. Tokens are saved to `token.json` / `token_<account>.json` (gitignored).

To run a digest immediately without waiting for the 5 PM scheduler:

```bash
python -m backend.main --now
```

### Gmail API setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** under APIs & Services → Library.
3. Create an **OAuth 2.0 Client ID** (Application type: Desktop app).
4. Download the JSON file and save it as `credentials.json` in the project root.
5. Run the app — it will open a browser for the consent screen per account and save `token.json`.

## API routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/accounts` | List configured Gmail accounts |
| GET | `/api/sample-text` | Headline + recommendations from the latest digest |
| GET | `/api/digests` | All digests (metadata only), newest first |
| GET | `/api/digests/latest` | Full latest digest JSON |
| GET | `/api/digests/status` | Whether a digest job is currently running |
| GET | `/api/digests/refresh` | Trigger a digest run (202, poll `/status` to track) |
| GET | `/api/digests/<filename>` | Specific digest by filename |
| POST | `/api/run` | Trigger a digest run in the background |

## Digest storage

Each run writes `digests/YYYY-MM-DD_HH-MM.json`. Same-day runs merge into today's file (new emails appended, recommendations combined). On the first run of a new day, emails from the previous calendar day are backfilled into the prior file; only emails received today start a new file.

## Roadmap

See [todo.md](todo.md) for the full task list. Up next:

- Importance feedback (thumbs up/down to evolve the algorithm)
- Push notifications for high-importance emails
- Outlook support
