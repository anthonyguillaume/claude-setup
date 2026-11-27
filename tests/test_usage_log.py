import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "tests"))

import usage_log  # noqa: E402
from test_gpt import FAKE  # noqa: E402


class UsageLogTest(unittest.TestCase):
    def setUp(self):
        self.log = Path(tempfile.mkdtemp(prefix="usage-")) / "usage.log"
        os.environ["AI_TEAM_USAGE_LOG"] = str(self.log)

    def tearDown(self):
        os.environ.pop("AI_TEAM_USAGE_LOG", None)

    def lines(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def test_record_appends_json_line(self):
        usage_log.record("gpt", "/p", True, 1.234, 42)
        usage_log.record("grok", None, False, 0.5, None)
        rows = self.lines()
        self.assertEqual(len(rows), 2)
        self.assertEqual({k: rows[0][k] for k in ("model", "project", "ok", "tokens")},
                         {"model": "gpt", "project": "/p", "ok": True, "tokens": 42})
        self.assertIn("at", rows[0])

    def test_record_never_raises(self):
        os.environ["AI_TEAM_USAGE_LOG"] = "/dev/null/impossible/usage.log"
        usage_log.record("gpt", None, True, 1, None)

    def _gpt(self, **env):
        bindir = Path(tempfile.mkdtemp(prefix="fakebin-"))
        (bindir / "codex").write_text(FAKE)
        (bindir / "codex").chmod(0o755)
        full = {**os.environ, "PATH": f"{bindir}:/usr/bin:/bin", "FAKE_LOG": str(bindir / "l.json"),
                "FAKE_ANSWER": "SECRET-ANSWER", "AI_TEAM_USAGE_LOG": str(self.log), **env}
        return subprocess.run([sys.executable, str(ROOT / "bin/gpt.py")], input="SECRET-PROMPT",
                              capture_output=True, text=True, env=full)

    def test_usage_log_has_no_content(self):
        r = self._gpt()
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.log.read_text()
        self.assertNotIn("SECRET-PROMPT", text)
        self.assertNotIn("SECRET-ANSWER", text)
        row = self.lines()[0]
        self.assertEqual((row["model"], row["ok"]), ("gpt", True))

    def test_failed_call_logged_not_ok(self):
        self._gpt(FAKE_EXIT="1")
        self.assertFalse(self.lines()[0]["ok"])


if __name__ == "__main__":
    unittest.main()
