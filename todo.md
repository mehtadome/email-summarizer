# TODO

## Done

- [x] Gmail email fetching via OAuth2 (`scripts/fetcher.py`)
- [x] Claude API summarization with importance scoring (`scripts/summarizer.py`)
- [x] Daily 5pm scheduler (`scripts/scheduler.py`)
- [x] FastAPI backend on port 8000 (`backend/api.py`)
- [x] JSON digest output saved to `digests/`
- [x] React + TypeScript frontend scaffolded (`frontend/`)
- [x] Vite dev proxy wired to backend (`/api` → `:8000`)
- [x] `GET /api/sample-text` — loads latest digest summary on page load
- [x] `POST /api/sample-text` — triggered by "Fetch digest info from backend" button
- [x] `GET /api/digests` — list all saved digests
- [x] `GET /api/digests/latest` — full latest digest
- [x] `POST /api/run` — trigger a digest run from the frontend

## Up Next

- [ ] Merge weekly digest files into one — instead of creating a new JSON each pull, merge the new emails into the existing weekly file and rename it to the latest pull time (e.g. pulling on Sunday at 5:44pm after a Wednesday pull produces a single `2026-04-13_17-44.json` containing all emails since Monday)
- [ ] Build out the digest browser UI (list + detail view for past digests)
- [ ] Evolve the importance algorithm with user feedback (thumbs up/down on digests)
- [ ] Configurable look-back window in the UI (e.g. weekend catchup → 72 hours)
- [ ] Push notifications when a high-importance email is detected (email or Slack)

## Future

- [ ] Outlook / Microsoft 365 support via Microsoft Graph API
  - Auth via MSAL (`msal` library), OAuth2 device-code flow
  - `GET /me/messages?$filter=receivedDateTime ge {timestamp}`
  - Add `scripts/fetcher_outlook.py` mirroring `fetcher.py`'s interface
  - Select provider via `EMAIL_PROVIDER=gmail|outlook` in `.env`
  - Reference: https://learn.microsoft.com/en-us/graph/api/user-list-messages
