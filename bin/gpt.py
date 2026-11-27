#!/usr/bin/env python3
"""Ask GPT through the Codex CLI on a filtered copy of the project.

Codex commands may only read that copy: no writes, no other file on the disk.

Usage: gpt.py [--project DIR [--diff BASE]] [--resume SESSION_ID] [--timeout 600] < prompt.txt
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
import usage_log  # noqa: E402

# filled by main(), written to the usage log on exit (counters only)
STATS = {"project": None, "tokens": None}


def fail(code: int, reason: str):
    print(f"GPT_UNAVAILABLE: {reason}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--resume")
    ap.add_argument("--diff", metavar="BASE", help="write the filtered BASE..HEAD diff to BRANCH.diff")
    ap.add_argument("--timeout", type=float, default=600)
    a = ap.parse_args()

    codex = shutil.which("codex")
    if not codex:
        fail(2, "codex not installed")
    prompt = sys.stdin.read()

    if a.diff and not a.project:
        fail(2, "--diff needs --project")
    if a.project:
        try:
            STATS["project"] = snapshot._scope(a.project)[0].as_posix()
            workdir = snapshot.make_snapshot(a.project)
            if a.diff:
                Path(workdir, "BRANCH.diff").write_text(snapshot.safe_diff(a.project, a.diff))
        except snapshot.NotGitRepo as e:
            fail(2, str(e))
    else:
        workdir = tempfile.mkdtemp(prefix="ai-snapshot-empty-")

    outdir = tempfile.mkdtemp(prefix="gpt-out-")
    for d in (workdir, outdir):
        atexit.register(shutil.rmtree, d, True)
    out = Path(outdir) / "last.txt"
    workdir = str(Path(workdir).resolve())
    # "--sandbox read-only" still lets commands read the whole disk (~/.ssh, other
    # projects): this permission profile only allows reading the snapshot
    # codex's sandbox helper must read its binary's directory (a file-only grant fails);
    # never grant a directory that is or contains the home directory
    bins = {str(Path(codex).parent.resolve()), str(Path(codex).resolve().parent)}
    home = Path.home().resolve()
    for d in bins:
        if home == Path(d) or Path(d) in home.parents:
            fail(2, f"codex is installed in {d}, which contains the home directory")
    # json.dumps gives a valid TOML basic string (quotes and backslashes escaped)
    readable = ",".join(f"{json.dumps(d)}=\"read\"" for d in sorted(bins | {workdir}))
    perms = ["-c", 'default_permissions="ai-team-readonly"',
             "-c", 'permissions.ai-team-readonly.filesystem='
                   f'{{":root"="deny",":minimal"="read",{readable}}}']
    # no user config (MCP servers, hooks run outside the sandbox), minimal env (no DB passwords)
    isolation = ["--ignore-user-config", "-c", 'shell_environment_policy.inherit="core"']
    # prompt on stdin ("-"): no argv size limit, not visible in ps, no "-" option confusion
    common = [*perms, *isolation, "--skip-git-repo-check", "--json", "-o", str(out)]
    if a.resume:
        cmd = [codex, "exec", "resume", *common, a.resume, "-"]
    else:
        cmd = [codex, "exec", "-C", workdir, *common, "-"]
    try:
        r = subprocess.run(cmd, cwd=workdir, input=prompt, capture_output=True, text=True,
                           timeout=a.timeout)
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
        u = ev.get("usage") if isinstance(ev, dict) else None
        if isinstance(u, dict):
            STATS["tokens"] = (STATS["tokens"] or 0) + u.get("input_tokens", 0) + u.get("output_tokens", 0)
    answer = out.read_text() if out.exists() else ""
    if not answer.strip():
        fail(3, "empty answer")
    print(answer)
    print(f"SESSION: {session}", file=sys.stderr)


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
        usage_log.record("gpt", STATS["project"], code == 0, time.monotonic() - t0, STATS["tokens"])
