import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class BootstrapCheckTest(unittest.TestCase):
    def run_check(self, env):
        return subprocess.run(["bash", str(ROOT / "bootstrap.sh"), "--check"],
                              capture_output=True, text=True, env=env)

    def test_check_reports_missing_and_fails_on_empty_machine(self):
        home = tempfile.mkdtemp(prefix="home-")
        r = self.run_check({"HOME": home, "PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("MISSING codex", r.stdout)
        self.assertIn("MISSING claude", r.stdout)
        self.assertIn("MISSING XAI_API_KEY", r.stdout)

    def test_check_never_prints_key_value(self):
        home = tempfile.mkdtemp(prefix="home-")
        r = self.run_check({"HOME": home, "PATH": "/usr/bin:/bin", "XAI_API_KEY": "sk-very-secret"})
        self.assertIn("OK XAI_API_KEY", r.stdout)
        self.assertNotIn("sk-very-secret", r.stdout + r.stderr)

    def test_check_installs_nothing(self):
        home = tempfile.mkdtemp(prefix="home-")
        self.run_check({"HOME": home, "PATH": "/usr/bin:/bin"})
        self.assertEqual(os.listdir(home), [])


if __name__ == "__main__":
    unittest.main()
