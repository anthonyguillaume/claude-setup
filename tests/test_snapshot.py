import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

import snapshot  # noqa: E402


def make_repo(files, untracked=()):
    d = Path(tempfile.mkdtemp(prefix="repo-"))
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    for rel in untracked:
        (d / rel).write_text("x")
    subprocess.run(["git", "-C", str(d), "add", "-A", "--", *files.keys()], check=True)
    return d


class SnapshotTest(unittest.TestCase):
    def test_snapshot_copies_tracked_files(self):
        repo = make_repo({"src/a.py": "print(1)"})
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertEqual((out / "src/a.py").read_text(), "print(1)")

    def test_snapshot_skips_untracked(self):
        repo = make_repo({"a.py": "1"}, untracked=["notes.txt"])
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "notes.txt").exists())

    def test_snapshot_excludes_tracked_secrets(self):
        secrets = [".env", ".env.local", "deploy.pem", "id_rsa", "aws_credentials.json",
                   "config/my_secret.txt", "server.key"]
        repo = make_repo({**{s: "SECRET" for s in secrets}, "ok.py": "1"})
        out = Path(snapshot.make_snapshot(str(repo)))
        for s in secrets:
            self.assertFalse((out / s).exists(), s)
        self.assertTrue((out / "ok.py").exists())

    def test_snapshot_respects_aiignore(self):
        repo = make_repo({".aiignore": "private/\n", "private/x.md": "p", "pub.md": "p"})
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "private/x.md").exists())
        self.assertTrue((out / "pub.md").exists())

    def test_snapshot_does_not_follow_symlinks(self):
        repo = make_repo({"a.py": "1"})
        os.symlink("/etc", repo / "link")
        subprocess.run(["git", "-C", str(repo), "add", "link"], check=True)
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "link" / "hosts").exists())

    def test_snapshot_refuses_non_git_dir(self):
        d = tempfile.mkdtemp(prefix="nogit-")
        r = subprocess.run([sys.executable, str(ROOT / "bin/snapshot.py"), d],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a git repository", r.stderr)


if __name__ == "__main__":
    unittest.main()
