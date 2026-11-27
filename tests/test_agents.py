import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = sorted((ROOT / "agents").glob("*.md"))
EXPECTED = {
    "challenger": "sonnet", "product-owner": "fable", "front-react": "sonnet",
    "back-csharp": "sonnet", "back-node": "sonnet", "back-rust": "opus",
    "test-writer": "sonnet", "reviewer": "opus", "security": "opus",
    "qa": "sonnet", "doc-writer": "sonnet",
}
FORBIDDEN_CHARS = re.compile("[—·\U0001F300-\U0001FAFF☀-➿]")


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def split(value):
    return [s.strip() for s in value.split(",") if s.strip()]


class AgentsTest(unittest.TestCase):
    def test_all_expected_agents_exist(self):
        self.assertEqual({p.stem for p in AGENTS}, set(EXPECTED))

    def test_agents_frontmatter(self):
        for p in AGENTS:
            fm = frontmatter(p)
            self.assertEqual(fm.get("name"), p.stem)
            self.assertTrue(fm.get("description"), p.name)
            self.assertIn(fm.get("model"), {"fable", "opus", "sonnet", "haiku"}, p.name)

    def test_agents_models_match_spec(self):
        for p in AGENTS:
            self.assertEqual(frontmatter(p)["model"], EXPECTED[p.stem], p.name)

    def test_agents_skills_exist(self):
        known = set((ROOT / "manifest/skills.txt").read_text().split())
        known |= {"debate", "verify", "cycle"}
        for p in AGENTS:
            for s in split(frontmatter(p).get("skills", "")):
                self.assertIn(s, known, f"{p.name}: unknown skill {s}")

    def test_readonly_agents(self):
        for name in ("reviewer", "security"):
            tools = split(frontmatter(ROOT / f"agents/{name}.md").get("tools", ""))
            self.assertTrue(tools, name)
            self.assertNotIn("Edit", tools)
            self.assertNotIn("Write", tools)

    def test_no_forbidden_characters(self):
        files = AGENTS + list((ROOT / "skills").rglob("*.md")) + list((ROOT / "rules").glob("*.md"))
        for p in files:
            self.assertIsNone(FORBIDDEN_CHARS.search(p.read_text()), p)


if __name__ == "__main__":
    unittest.main()
