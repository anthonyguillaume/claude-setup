import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class LayoutTest(unittest.TestCase):
    def test_plugin_manifest(self):
        data = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(data["name"], "ai-team")
        self.assertIn("version", data)
        self.assertIn("description", data)

    def test_marketplace_lists_plugin(self):
        data = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(data["plugins"][0]["name"], "ai-team")
        self.assertEqual(data["plugins"][0]["source"], "./")


if __name__ == "__main__":
    unittest.main()
