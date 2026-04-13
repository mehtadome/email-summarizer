"""FastAPI server — exposes digest data and triggers to the frontend."""

import json
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Email summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_DIGESTS_DIR = Path(__file__).parent.parent / "digests"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_digest_paths() -> list[Path]:
    if not _DIGESTS_DIR.exists():
        return []
    return sorted(_DIGESTS_DIR.glob("*.json"), reverse=True)


def _load_digest(path: Path) -> dict:
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "message": "Email summarizer API is running."}


@app.post("/api/sample-text")
def post_sample_text() -> dict[str, str]:
    """Returns a hardcoded sample text — used to verify the POST flow end-to-end."""
    return {"text": "Hello from the backend! POST is working."}


def _sample_text_payload(digest: dict | None, empty_message: str | None = None) -> dict:
    """
    Build JSON for GET /api/sample-text: title + recommendations from overall_summary,
    or legacy plain string / empty state.
    """
    if digest is None:
        return {
            "title": None,
            "recommendations": [],
            "message": empty_message or "No digest yet — run `python -m backend.main --now` to generate one.",
        }

    osum = digest.get("overall_summary")
    if isinstance(osum, dict):
        title = osum.get("title")
        if title is not None and not isinstance(title, str):
            title = str(title)
        raw_recs = osum.get("recommendations", [])
        if not isinstance(raw_recs, list):
            raw_recs = []
        recommendations = [str(x).strip() for x in raw_recs if str(x).strip()]
        return {
            "title": title or "",
            "recommendations": recommendations,
        }
    if isinstance(osum, str) and osum.strip():
        return {
            "title": None,
            "recommendations": [],
            "legacy_text": osum,
        }
    return {
        "title": None,
        "recommendations": [],
        "message": "(no summary)",
    }


@app.get("/api/sample-text")
def sample_text() -> dict:
    """
    Overall digest headline + recommendation list from the latest file, or a status message.
    """
    paths = _all_digest_paths()
    if not paths:
        return _sample_text_payload(None)

    digest = _load_digest(paths[0])
    return _sample_text_payload(digest)


@app.get("/api/digests")
def list_digests() -> list[dict]:
    """Return metadata for all saved digests, newest first."""
    result = []
    for p in _all_digest_paths():
        try:
            d = _load_digest(p)
            result.append({
                "filename": p.name,
                "generated_at": d.get("generated_at"),
                "total_emails": d.get("total_emails", 0),
                "overall_summary": d.get("overall_summary", ""),
            })
        except Exception:
            pass
    return result


@app.get("/api/digests/latest")
def latest_digest() -> dict:
    """Return the newest digest JSON on disk (does not run the pipeline)."""
    paths = _all_digest_paths()
    if not paths:
        raise HTTPException(status_code=404, detail="No digests found.")
    return _load_digest(paths[0])


@app.get("/api/digests/{filename}")
def get_digest(filename: str) -> dict:
    """Return a specific digest by filename (e.g. 2026-04-12_17-00.json)."""
    path = _DIGESTS_DIR / Path(filename).name
    if not path.exists() or path.suffix != ".json":
        raise HTTPException(status_code=404, detail=f"Digest '{filename}' not found.")
    return _load_digest(path)


@app.post("/api/run", status_code=202)
def trigger_run() -> dict[str, str]:
    """Kick off a digest run in a background thread and return immediately."""
    from backend.main import run_digest

    def _run():
        try:
            run_digest()
        except Exception as exc:
            print(f"[api] run_digest error: {exc}")

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def start(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run("backend.api:app", host=host, port=port, reload=True)
