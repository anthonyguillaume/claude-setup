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

# Matched case-insensitively against the file name.
EXCLUDE_PATTERNS = [
    ".env*", "*.pem", "*.key", "*.p12", "*.pfx", "*.keystore", "*.jks", "*.kdbx",
    "*.tfstate", "*.tfstate.*", "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",
    "*credentials*", "*secret*", ".npmrc", ".netrc", ".pypirc", ".htpasswd",
    "appsettings.*.json", "*.tfvars", "*.ppk", ".kube", "kubeconfig", ".dockercfg",
]


class NotGitRepo(Exception):
    pass


def _git_files(src: Path, *args: str) -> set[str]:
    r = subprocess.run(["git", "-C", str(src), "ls-files", "-z", *args], capture_output=True)
    if r.returncode != 0:
        raise NotGitRepo(f"{src} is not a git repository")
    return set(filter(None, r.stdout.decode().split("\0")))


def _is_secret(rel: str) -> bool:
    # every path component, so secrets/ and credentials/ dirs are excluded too
    return any(fnmatch.fnmatchcase(part, p)
               for part in rel.lower().split("/") for p in EXCLUDE_PATTERNS)


def _scope(project_dir: str) -> tuple[Path, str]:
    target = Path(project_dir).resolve()
    r = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise NotGitRepo(f"{project_dir} is not a git repository")
    # paths stay relative to the repo root so .aiignore rules anchor correctly,
    # but only files under the requested directory are listed
    src = Path(r.stdout.strip()).resolve()
    return src, str(target.relative_to(src)) or "."


def _aiignored(src: Path, scope: str) -> set[str]:
    # git applies every .aiignore (root and nested) with gitignore semantics
    return _git_files(src, "--cached", "--ignored", "--exclude-per-directory=.aiignore",
                      "--", scope)


def make_snapshot(project_dir: str) -> str:
    src, scope = _scope(project_dir)
    files = _git_files(src, "--", scope) - _aiignored(src, scope)
    dest = Path(tempfile.mkdtemp(prefix="ai-snapshot-"))
    for rel in files:
        path = src / rel
        # symlinks skipped, also symlinked parent dirs: they could point outside the repo
        if (_is_secret(rel) or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(src)):
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest / rel, follow_symlinks=False)
    return str(dest)


def safe_diff(project_dir: str, base: str) -> str:
    """git diff base..HEAD limited to files the snapshot would include."""
    src, scope = _scope(project_dir)
    r = subprocess.run(["git", "-C", str(src), "diff", "--name-only", "-z", f"{base}..HEAD",
                        "--", scope], capture_output=True)
    if r.returncode != 0:
        raise NotGitRepo(f"cannot diff {base}..HEAD in {src}")
    # shortcut: .aiignore is checked against the current index, so a file deleted on the
    # branch is only filtered by name patterns; upgrade if .aiignore'd files get deleted
    ignored = _aiignored(src, scope)
    keep = [f for f in filter(None, r.stdout.decode().split("\0"))
            if not _is_secret(f) and f not in ignored]
    if not keep:
        return ""
    r = subprocess.run(["git", "-C", str(src), "diff", f"{base}..HEAD", "--", *keep],
                       capture_output=True, text=True)
    return r.stdout


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: snapshot.py <project_dir>")
    try:
        print(make_snapshot(sys.argv[1]))
    except NotGitRepo as e:
        print(f"snapshot: {e}", file=sys.stderr)
        sys.exit(2)
