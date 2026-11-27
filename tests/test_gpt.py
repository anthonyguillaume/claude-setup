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
    if args and args[-1] == "-":
        sys.stdin.read()
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
        self.assertNotIn("--sandbox", log["args"])
        self.assertIn('default_permissions="ai-team-readonly"', joined)
        self.assertIn('":root"="deny"', joined)
        self.assertRegex(joined, r'"[^"]*ai-snapshot-[^"]*"="read"')
        self.assertIn(f'"{self.bindir.resolve()}"="read"', joined)
        self.assertNotIn(str(repo.resolve()), joined + log["cwd"])

    def test_gpt_isolates_user_config_and_environment(self):
        r = self.run_gpt()
        self.assertEqual(r.returncode, 0, r.stderr)
        joined = " ".join(self.logged()["args"])
        self.assertIn("--ignore-user-config", joined)
        self.assertIn('shell_environment_policy.inherit="core"', joined)

    def test_gpt_reads_prompt_from_stdin_not_argv(self):
        big = "-" + "x" * 2_000_000
        r = self.run_gpt(prompt=big)
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.logged()["args"]
        self.assertEqual(args[-1], "-")
        self.assertNotIn(big, args)

    def test_gpt_diff_written_into_snapshot(self):
        repo = Path(tempfile.mkdtemp(prefix="repo-"))
        git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "a.py").write_text("1")
        subprocess.run(git + ["add", "a.py"], check=True)
        subprocess.run(git + ["commit", "-qm", "b"], check=True)
        base = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        (repo / "a.py").write_text("2")
        subprocess.run(git + ["commit", "-qam", "c"], check=True)
        fake = self.bindir / "codex"
        fake.write_text(FAKE.replace("time.sleep(", "open(os.environ['FAKE_LOG'] + '.diff', 'w').write(open('BRANCH.diff').read()); time.sleep("))
        r = self.run_gpt("--project", str(repo), "--diff", base)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("a.py", (self.bindir / "log.json.diff").read_text())

    def test_gpt_resume_passes_session(self):
        r = self.run_gpt("--resume", "abc")
        self.assertEqual(r.returncode, 0, r.stderr)
        args = self.logged()["args"]
        self.assertIn("resume", args)
        self.assertIn("abc", args)
        self.assertIn('":root"="deny"', " ".join(args))

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
