#!/usr/bin/env python3
"""Ask Grok through the xAI API (OpenAI-compatible). Sends only the prompt text.

Usage: grok.py [--model M] [--timeout 300] < prompt.txt
Env: XAI_API_KEY (required), XAI_BASE_URL, XAI_MODEL.
Exit: 0 ok, 2 config problem, 3 Grok unavailable. The key is never printed.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import usage_log  # noqa: E402

TOKENS = {"n": None}

# shortcut: default model name set from memory, check docs.x.ai if xAI renames it
DEFAULT_MODEL = "grok-4"


def fail(code: int, reason: str):
    print(f"GROK_UNAVAILABLE: {reason}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("XAI_MODEL", DEFAULT_MODEL))
    ap.add_argument("--timeout", type=float, default=300)
    a = ap.parse_args()

    key = os.environ.get("XAI_API_KEY")
    if not key:
        fail(2, "XAI_API_KEY not set")
    base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
    body = json.dumps({"model": a.model,
                       "messages": [{"role": "user", "content": sys.stdin.read()}]}).encode()
    req = urllib.request.Request(f"{base}/chat/completions", data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        fail(3, f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError) as e:
        fail(3, f"network error {type(e).__name__}")
    if isinstance(data, dict) and isinstance(data.get("usage"), dict):
        TOKENS["n"] = data["usage"].get("total_tokens")
    try:
        print(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError):
        fail(3, "unexpected response format")


if __name__ == "__main__":
    import time
    t0 = time.monotonic()
    code = 0
    try:
        main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        raise
    finally:
        # Grok never gets project files: no project in its counters
        usage_log.record("grok", None, code == 0, time.monotonic() - t0, TOKENS["n"])
