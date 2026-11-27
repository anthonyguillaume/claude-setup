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

    def test_snapshot_excludes_secrets_case_insensitive_and_more_types(self):
        secrets = [".ENV", "Prod.PEM", "cert.p12", "store.pfx", ".npmrc", ".netrc",
                   ".pypirc", "app.keystore", "infra/terraform.tfstate", "vault.kdbx"]
        repo = make_repo({**{s: "SECRET" for s in secrets}, "ok.py": "1"})
        out = Path(snapshot.make_snapshot(str(repo)))
        for s in secrets:
            self.assertFalse((out / s).exists(), s)

    def test_snapshot_excludes_files_inside_secret_dirs(self):
        repo = make_repo({"secrets/db.yml": "x", "config/credentials/aws.json": "x", "ok.py": "1"})
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "secrets/db.yml").exists())
        self.assertFalse((out / "config/credentials/aws.json").exists())
        self.assertTrue((out / "ok.py").exists())

    def test_snapshot_from_subdir_uses_repo_root_rules(self):
        repo = make_repo({".aiignore": "/app/private.md\n", "app/private.md": "x", "app/ok.md": "x"})
        out = Path(snapshot.make_snapshot(str(repo / "app")))
        self.assertFalse((out / "app/private.md").exists())
        self.assertTrue((out / "app/ok.md").exists())

    def test_snapshot_of_subdir_excludes_siblings(self):
        repo = make_repo({"app/a.py": "1", "other/b.py": "2"})
        out = Path(snapshot.make_snapshot(str(repo / "app")))
        self.assertTrue((out / "app/a.py").exists())
        self.assertFalse((out / "other/b.py").exists())

    def test_snapshot_applies_nested_aiignore(self):
        repo = make_repo({"app/.aiignore": "hidden.md\n", "app/hidden.md": "x", "app/ok.md": "x"})
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "app/hidden.md").exists())
        self.assertTrue((out / "app/ok.md").exists())

    def test_snapshot_aiignore_uses_gitignore_semantics(self):
        repo = make_repo({".aiignore": "*.sql\n/top.md\n", "db/dump.sql": "x",
                          "top.md": "x", "docs/top.md": "x"})
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "db/dump.sql").exists())
        self.assertFalse((out / "top.md").exists())
        self.assertTrue((out / "docs/top.md").exists())

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

    def test_snapshot_does_not_follow_symlinked_parent_dir(self):
        outside = Path(tempfile.mkdtemp(prefix="outside-"))
        (outside / "app.json").write_text("TOPSECRET")
        repo = make_repo({"conf/app.json": "ok", "a.py": "1"})
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "x"], check=True)
        (repo / "conf/app.json").unlink()
        (repo / "conf").rmdir()
        os.symlink(outside, repo / "conf")
        out = Path(snapshot.make_snapshot(str(repo)))
        self.assertFalse((out / "conf/app.json").exists())

    def test_snapshot_excludes_dotnet_terraform_and_kube_secrets(self):
        secrets = ["appsettings.Production.json", "src/Api/appsettings.Development.json",
                   "infra/prod.tfvars", "key.ppk", ".kube/config", "kubeconfig", ".dockercfg"]
        repo = make_repo({**{s: "SECRET" for s in secrets}, "appsettings.json": "{}"})
        out = Path(snapshot.make_snapshot(str(repo)))
        for s in secrets:
            self.assertFalse((out / s).exists(), s)
        self.assertTrue((out / "appsettings.json").exists())

    def test_safe_diff_excludes_secrets_and_aiignore(self):
        repo = make_repo({"a.py": "1", ".aiignore": "private.md\n"})
        git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(git + ["commit", "-qm", "base"], check=True)
        base = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        (repo / "a.py").write_text("2")
        (repo / ".env").write_text("PASSWORD=hunter2")
        (repo / "private.md").write_text("PRIVATE")
        subprocess.run(git + ["add", "-f", "a.py", ".env", "private.md"], check=True)
        subprocess.run(git + ["commit", "-qm", "change"], check=True)
        diff = snapshot.safe_diff(str(repo), base)
        self.assertIn("a.py", diff)
        self.assertNotIn("hunter2", diff)
        self.assertNotIn("PRIVATE", diff)

    def _two_commits(self, before, after):
        repo = make_repo(before)
        git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(git + ["commit", "-qm", "base"], check=True)
        base = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        after(repo, git)
        subprocess.run(git + ["add", "-A", "-f"], check=True)
        subprocess.run(git + ["commit", "-qm", "change"], check=True)
        return repo, base

    def test_safe_diff_hides_deleted_aiignored_file(self):
        def after(repo, git):
            (repo / "private.md").unlink()
        repo, base = self._two_commits({".aiignore": "private.md\n", "private.md": "PRIVATE"}, after)
        self.assertNotIn("PRIVATE", snapshot.safe_diff(str(repo), base))

    def test_safe_diff_filenames_are_literal_not_globs(self):
        def after(repo, git):
            (repo / ".env").write_text("PASSWORD=hunter2")
            (repo / ".e*").write_text("2")
        repo, base = self._two_commits({".env": "PASSWORD=old", ".e*": "1"}, after)
        self.assertNotIn("hunter2", snapshot.safe_diff(str(repo), base))

    def test_snapshot_refuses_non_git_dir(self):
        d = tempfile.mkdtemp(prefix="nogit-")
        r = subprocess.run([sys.executable, str(ROOT / "bin/snapshot.py"), d],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a git repository", r.stderr)


if __name__ == "__main__":
    unittest.main()
