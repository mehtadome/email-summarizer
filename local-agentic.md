# Local Agentic Development (No API Key)

Patterns and gotchas for building Claude-powered apps locally using a Claude Pro subscription instead of an Anthropic API key.

---

## How it works

Claude Code ships a CLI (`claude`) that authenticates via OAuth against your Pro subscription. You can call it programmatically as a subprocess — no `ANTHROPIC_API_KEY` needed.

```bash
claude -p "your prompt here"
```

---

## Calling the CLI from Python

```python
import os
import subprocess

def call_claude(prompt: str) -> str:
    # Strip ANTHROPIC_API_KEY so the CLI falls back to OAuth keychain auth.
    # If the key is present in the environment (even blank), the CLI treats it
    # as the auth method and rejects it. See the "Gotchas" section below.
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    result = subprocess.run(
        ["/opt/homebrew/bin/claude", "-p", "--no-session-persistence"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (rc={result.returncode})\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )

    return result.stdout.strip()
```

**Key flags:**
- `-p` / `--print` — non-interactive mode, prints response and exits
- `--no-session-persistence` — don't save this as a resumable session
- `input=prompt` — pass the prompt via stdin (avoids shell arg length limits for large prompts)

---

## Finding the CLI path

```bash
which claude
# → /opt/homebrew/bin/claude  (Homebrew on Apple Silicon)
# → /usr/local/bin/claude     (Homebrew on Intel Mac)
```

Use the full path in subprocess calls — child processes may not inherit your shell's `PATH`.

---

## Gotchas

### 1. `ANTHROPIC_API_KEY` in the environment overrides OAuth

If `ANTHROPIC_API_KEY` is set in the parent process (e.g. loaded from a `.env` file via `python-dotenv`), the Claude CLI inherits it and tries to use it as the auth method — even if it's blank or a placeholder. This causes:

```
Invalid API key · Fix external API key
```

**Fix:** Strip the key from the subprocess environment before spawning the CLI:

```python
env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
```

### 2. Large prompts must go via stdin, not argv

Passing a large prompt as a CLI argument (`claude -p "...huge string..."`) can fail silently when the argument exceeds shell limits. Use `input=` to pipe via stdin instead.

### 3. Event loop conflicts when calling from FastAPI/uvicorn

If you use `claude-agent-sdk` (the async SDK), calling `asyncio.run()` inside a uvicorn worker fails because uvicorn already owns the event loop. The subprocess approach sidesteps this entirely — no async, no loop conflicts.

### 4. Subprocess-of-subprocess still works

If uvicorn spawns `python -m yourapp --now` as a subprocess, and that process spawns `claude -p`, the auth still works as long as `ANTHROPIC_API_KEY` is stripped at each level.

---

## Alternative: claude-agent-sdk

The `claude-agent-sdk` package (`pip install claude-agent-sdk`) provides an async Python interface:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def ask_claude(prompt: str, system: str) -> str:
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(system_prompt=system, max_turns=1)
    ):
        if isinstance(message, ResultMessage):
            return message.result or ""
    return ""
```

**When to use:** Works well for standalone async scripts (see `todo-manager/todo_manager.py`).  
**When to avoid:** Breaks inside a running event loop (FastAPI, uvicorn). Use the subprocess approach instead.

---

## Reference projects

| Project | Approach | Notes |
|---|---|---|
| `email-summarizer` | `subprocess` calling `claude -p` | Avoids event loop issues with FastAPI |
| `todo-manager` | `claude-agent-sdk` async | Standalone CLI script, no web server |
