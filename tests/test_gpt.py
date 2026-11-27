import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPT = ROOT / "bin/gpt.py"

FAKE = textwrap.dedent(f"""\
    #!{sys.executable}
    import json, os, sys, time
    args = sys.argv[1:]
    with open(os.environ["FAKE_LOG"], "w") as f:
        json.dump({{"args": args, "cwd": os.getcwd()}}, f)
    time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
    if "-o" in args:
        open(args[args.index("-o") + 1], "w").write(os.environ.get("FAKE_ANSWER", ""))
    print(json.dumps({{"type": "thread.started", "thread_id": "abc"}}))
    if os.environ.get("FAKE_STDERR"):
        print(os.environ["FAKE_STDERR"], file=sys.stderr)
    sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
""")


class GptTest(unittest.TestCase):
    def setUp(self):
        self.bindir = Path(tempfile.mkdtemp(prefix="fakebin-"))
        fake = self.bindir / "codex"
        fake.write_text(FAKE)
        fake.chmod(0o755)
        self.log = self.bindir / "log.json"
        self.env = {**os.environ, "PATH": f"{self.bindir}:/usr/bin:/bin",
                    "FAKE_LOG": str(self.log), "FAKE_ANSWER": "réponse"}

    def run_gpt(self, *args, prompt="question", **env):
        return subprocess.run([sys.executable, str(GPT), *args], input=prompt,
                              capture_output=True, text=True, env={**self.env, **env})

    def logged(self):
        return json.loads(self.log.read_text())

    def test_gpt_returns_answer(self):
        r = self.run_gpt()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "réponse")
        self.assertIn("SESSION: abc", r.stderr)

    def test_gpt_runs_read_only_in_snapshot(self):
        repo = Path(tempfile.mkdtemp(prefix="repo-"))
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "a.py").write_text("1")
        subprocess.run(["git", "-C", str(repo), "add", "a.py"], check=True)
        r = self.run_gpt("--project", str(repo))
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.logged()
        joined = " ".join(log["args"])
        self.assertIn("read-only", joined)
        self.assertIn("ai-snapshot-", joined)
        self.assertNotIn(str(repo.resolve()), joined + log["cwd"])

    def test_gpt_resume_passes_session(self):
        r = self.run_gpt("--resume", "abc")
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.logged()["args"]
        self.assertIn("resume", args)
        self.assertIn("abc", args)
        self.assertIn('sandbox_mode="read-only"', " ".join(args))

    def test_gpt_missing_codex(self):
        r = self.run_gpt(PATH="/usr/bin:/bin")
        self.assertEqual(r.returncode, 2)
        self.assertIn("GPT_UNAVAILABLE: codex not installed", r.stderr)

    def test_gpt_unavailable_on_codex_error(self):
        r = self.run_gpt(FAKE_EXIT="1", FAKE_STDERR="Not logged in")
        self.assertEqual(r.returncode, 3)
        self.assertIn("GPT_UNAVAILABLE:", r.stderr)
        self.assertIn("Not logged in", r.stderr)

    def test_gpt_timeout(self):
        r = self.run_gpt("--timeout", "1", FAKE_SLEEP="5")
        self.assertEqual(r.returncode, 3)
        self.assertIn("GPT_UNAVAILABLE: timeout", r.stderr)

    def test_gpt_project_not_git_degrades(self):
        r = self.run_gpt("--project", tempfile.mkdtemp(prefix="nogit-"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("GPT_UNAVAILABLE:", r.stderr)


if __name__ == "__main__":
    unittest.main()
