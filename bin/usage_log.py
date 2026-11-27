"""Counters for GPT and Grok calls, read by the dashboard. Never the prompt or the answer."""
import datetime as dt
import json
import os
from pathlib import Path


def record(model: str, project, ok: bool, seconds: float, tokens) -> None:
    path = Path(os.environ.get("AI_TEAM_USAGE_LOG", "~/.ai-team/usage.log")).expanduser()
    row = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "model": model,
           "project": project, "ok": ok, "seconds": round(seconds, 1), "tokens": tokens}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass  # the log is optional: a call must never fail because of it
