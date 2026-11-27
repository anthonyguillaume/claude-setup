#!/usr/bin/env python3
"""Filtered copy of a git project for external models (GPT, DeepSeek).

Only git-tracked files, never secrets, never symlinks.
Usage: snapshot.py <project_dir>  -> prints the snapshot path.
"""
import fnmatch
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXCLUDE_PATTERNS = [".env*", "*.pem", "*.key", "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*", "*credentials*", "*secret*"]


class NotGitRepo(Exception):
    pass


def _excluded(rel: str, extra: list[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    for pat in EXCLUDE_PATTERNS + extra:
        if pat.endswith("/"):
            if rel.startswith(pat) or f"/{pat}" in f"/{rel}":
                return True
        elif fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat):
            return True
    return False


def make_snapshot(project_dir: str) -> str:
    src = Path(project_dir).resolve()
    r = subprocess.run(["git", "-C", str(src), "ls-files", "-z"], capture_output=True)
    if r.returncode != 0:
        raise NotGitRepo(f"{src} is not a git repository")
    aiignore = src / ".aiignore"
    extra = []
    if aiignore.is_file():
        extra = [l.strip() for l in aiignore.read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
    dest = Path(tempfile.mkdtemp(prefix="ai-snapshot-"))
    for rel in filter(None, r.stdout.decode().split("\0")):
        path = src / rel
        # symlinks skipped: they could point outside the repo (~/.ssh...)
        if _excluded(rel, extra) or path.is_symlink() or not path.is_file():
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest / rel, follow_symlinks=False)
    return str(dest)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: snapshot.py <project_dir>")
    try:
        print(make_snapshot(sys.argv[1]))
    except NotGitRepo as e:
        print(f"snapshot: {e}", file=sys.stderr)
        sys.exit(2)
