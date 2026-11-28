import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "docs/superpowers/specs/2026-11-28-dev-rules-inventory.md"

CORE = {"index", "git", "testing", "security", "api-rest", "i18n", "skills"}
BACK = CORE | {"database-postgres", "docker-ops"}


def r(*names):
    return {f"ai-team:rules-{n}" for n in names}


MATRIX = {
    "front-react": r(*CORE, "frontend-react", "ui"),
    "back-csharp": r(*BACK, "backend-dotnet"),
    "back-node": r(*BACK, "backend-node"),
    "back-python": r(*BACK, "backend-python"),
    "back-rust": r(*BACK, "backend-rust"),
    "test-writer": r("index", "git", "testing", "i18n"),
    "reviewer": r(*BACK, "frontend-react", "ui"),
    "security": r("index", "security", "api-rest", "database-postgres", "docker-ops"),
    "qa": r("index", "ui", "i18n", "testing"),
    "doc-writer": r("index", "git"),
    "challenger": set(), "product-owner": set(),
}

NON_PACK = ["index", "git", "testing", "security", "api-rest", "database-postgres",
            "docker-ops", "backend-dotnet", "backend-node", "backend-python",
            "backend-rust", "frontend-react", "ui", "i18n", "skills"]
PROJECT_NAMES = re.compile(r"\b(orbital|orbitalinvest|bowtrail|velzon|tenant|locataire)\b", re.I)


def inventory():
    sections, current = {}, None
    for line in INVENTORY.read_text().splitlines():
        m = re.match(r"^## (rules-\S+)", line)
        if m:
            current = sections.setdefault(m.group(1), [])
            continue
        m = re.match(r"^- (AT-[A-Z0-9]+-\d+) \(", line)
        if m and current is not None:
            current.append(m.group(1))
    return sections


def skill_path(name):
    return ROOT / "skills" / name / "SKILL.md"


class RulesTest(unittest.TestCase):
    def check_skill(self, name):
        path = skill_path(name)
        self.assertTrue(path.exists(), f"{name}: SKILL.md manquant")
        text = path.read_text()
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        self.assertTrue(m, f"{name}: pas de frontmatter")
        fm = dict(x.groups() for x in (re.match(r"(\w+):\s*(.*)", l) for l in m.group(1).splitlines()) if x)
        self.assertEqual(fm.get("name"), name)
        self.assertRegex(fm.get("description", ""), r'^".+"$', f"{name}: description entre guillemets")
        lines = text.splitlines()
        self.assertLessEqual(len(lines), 110, f"{name}: {len(lines)} lignes")
        ids = []
        for l in lines:
            if l.startswith("- **AT-"):
                rm = re.match(r"^- \*\*(AT-[A-Z0-9]+-\d+)\*\* \S", l)
                self.assertTrue(rm, f"{name}: ligne mal formée: {l[:60]}")
                ids.append(rm.group(1))
        self.assertEqual(len(ids), len(set(ids)), f"{name}: doublons")
        self.assertEqual(text.count("**AT-"), len(ids), f"{name}: identifiant en gras hors ligne de règle")
        self.assertEqual(set(ids), set(inventory()[name]), f"{name}: identifiants")

    def check_group(self, names):
        for name in names:
            with self.subTest(skill=name):
                self.check_skill(name)

    def test_skill_dirs_match_inventory(self):
        dirs = {d.name for d in (ROOT / "skills").glob("rules-*") if d.is_dir()}
        self.assertEqual(dirs, set(inventory()))

    def test_core_skills(self):
        self.check_group(["rules-index", "rules-git", "rules-skills"])

    def test_testing_security(self):
        self.check_group(["rules-testing", "rules-security"])

    def test_back_shared(self):
        self.check_group(["rules-api-rest", "rules-database-postgres", "rules-docker-ops"])

    def test_backends(self):
        self.check_group(["rules-backend-dotnet", "rules-backend-node",
                          "rules-backend-python", "rules-backend-rust"])

    def test_front(self):
        self.check_group(["rules-frontend-react", "rules-ui", "rules-i18n"])

    def test_packs(self):
        self.check_group(["rules-pack-multitenant-postgres", "rules-pack-audit-trail"])

    def test_index_mentions_packs(self):
        path = skill_path("rules-index")
        self.assertTrue(path.exists(), "rules-index manquant")
        text = path.read_text()
        for needle in ("Packs ai-team :", "rules-pack-multitenant-postgres",
                       "rules-pack-audit-trail", "outil Skill"):
            self.assertIn(needle, text)

    def test_total_budget(self):
        total = 0
        for n in NON_PACK:
            path = skill_path(f"rules-{n}")
            self.assertTrue(path.exists(), f"rules-{n} manquant")
            total += len(path.read_text().splitlines())
        self.assertLessEqual(total, 950)

    def test_no_project_names(self):
        for d in (ROOT / "skills").glob("rules-*"):
            path = d / "SKILL.md"
            if d.name.startswith("rules-pack-") or not path.exists():
                continue
            self.assertIsNone(PROJECT_NAMES.search(path.read_text()), d.name)

    def test_agent_rules_matrix(self):
        self.assertEqual({p.stem for p in (ROOT / "agents").glob("*.md")}, set(MATRIX))
        for p in sorted((ROOT / "agents").glob("*.md")):
            fm = re.match(r"---\n(.*?)\n---\n", p.read_text(), re.S).group(1)
            m = re.search(r"^skills:\s*(.*)$", fm, re.M)
            skills = {s.strip() for s in m.group(1).split(",") if s.strip()} if m else set()
            got = {s for s in skills if s.startswith("ai-team:rules-")}
            self.assertEqual(got, MATRIX[p.stem], p.name)


if __name__ == "__main__":
    unittest.main()
