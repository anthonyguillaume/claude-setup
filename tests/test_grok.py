import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROK = ROOT / "bin/grok.py"


class FakeXai(BaseHTTPRequestHandler):
    status = 200
    seen = {}

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        FakeXai.seen = {"path": self.path, "auth": self.headers.get("Authorization"),
                        "body": json.loads(body)}
        self.send_response(FakeXai.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = {"choices": [{"message": {"content": "salut"}}]} if FakeXai.status == 200 \
            else {"error": "rate limited"}
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *a):
        pass


class GrokTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeXai)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def run_grok(self, env):
        base = {k: v for k, v in os.environ.items() if k != "XAI_API_KEY"}
        return subprocess.run([sys.executable, str(GROK)], input="bonjour",
                              capture_output=True, text=True,
                              env={**base, "XAI_BASE_URL": self.base, **env})

    def test_grok_returns_answer(self):
        FakeXai.status = 200
        r = self.run_grok({"XAI_API_KEY": "test-key"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "salut")
        self.assertEqual(FakeXai.seen["path"], "/v1/chat/completions")
        self.assertEqual(FakeXai.seen["auth"], "Bearer test-key")
        self.assertEqual(FakeXai.seen["body"]["messages"][-1]["content"], "bonjour")

    def test_grok_missing_key(self):
        r = self.run_grok({})
        self.assertEqual(r.returncode, 2)
        self.assertIn("GROK_UNAVAILABLE: XAI_API_KEY not set", r.stderr)

    def test_grok_http_error_hides_key(self):
        FakeXai.status = 429
        r = self.run_grok({"XAI_API_KEY": "test-key"})
        self.assertEqual(r.returncode, 3)
        self.assertIn("GROK_UNAVAILABLE: HTTP 429", r.stderr)
        self.assertNotIn("test-key", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
