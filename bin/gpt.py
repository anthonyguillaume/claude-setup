#!/usr/bin/env python3
"""Ask GPT through the Codex CLI, read-only, on a filtered copy of the project.

Usage: gpt.py [--project DIR] [--resume SESSION_ID] [--timeout 600] < prompt.txt
stdout: GPT's last answer. stderr last line: "SESSION: <id>".
Exit: 0 ok, 2 config problem (codex missing, not a git repo), 3 GPT unavailable.
"""
import argparse
import atexit
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import snapshot  # noqa: E402


def fail(code: int, reason: str):
    print(f"GPT_UNAVAILABLE: {reason}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--resume")
    ap.add_argument("--timeout", type=float, default=600)
    a = ap.parse_args()

    codex = shutil.which("codex")
    if not codex:
        fail(2, "codex not installed")
    prompt = sys.stdin.read()

    if a.project:
        try:
            workdir = snapshot.make_snapshot(a.project)
        except snapshot.NotGitRepo as e:
            fail(2, str(e))
    else:
        workdir = tempfile.mkdtemp(prefix="ai-snapshot-empty-")

    outdir = tempfile.mkdtemp(prefix="gpt-out-")
    for d in (workdir, outdir):
        atexit.register(shutil.rmtree, d, True)
    out = Path(outdir) / "last.txt"
    if a.resume:
        # resume has no --sandbox/--cd flags: sandbox via config, cwd via process
        cmd = [codex, "exec", "resume", "-c", 'sandbox_mode="read-only"',
               "--skip-git-repo-check", "--json", "-o", str(out), a.resume, prompt]
    else:
        cmd = [codex, "exec", "--sandbox", "read-only", "-C", workdir,
               "--skip-git-repo-check", "--json", "-o", str(out), prompt]
    try:
        r = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        fail(3, "timeout")
    if r.returncode != 0:
        fail(3, (r.stderr.strip() or r.stdout.strip())[-500:] or f"codex exit {r.returncode}")

    session = a.resume
    for line in r.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "thread.started":
            session = ev.get("thread_id")
    answer = out.read_text() if out.exists() else ""
    if not answer.strip():
        fail(3, "empty answer")
    print(answer)
    print(f"SESSION: {session}", file=sys.stderr)


if __name__ == "__main__":
    main()
