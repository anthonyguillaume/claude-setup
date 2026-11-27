"""Tests du collecteur du tableau de suivi (rules/dashboard.md, DASH-02).

Python stdlib seulement. Les fixtures sont construites dans un dossier temporaire et `sources` est
assemblé à la main : build_board() ne fait aucune E/S, aucun test ne lit les vrais journaux, le vrai dépôt
ni ~/.deepseek-mcp, et aucun ne lance de commande gh ou git.
Usage : python3 -I -m unittest discover -s scripts/dashboard -p 'test_*.py' -v
(`python3 -I` ignore PYTHONPATH et n'ajoute pas le dossier courant : voir `_charger_collect`.)
"""
import json
import os
import tempfile
import unittest


def _charger_collect():
    """Importe collect.py par son chemin : `python3 -I` ignore PYTHONPATH et n'ajoute pas le dossier courant."""
    import importlib.util
    chemin = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "dashboard_collect.py")
    spec = importlib.util.spec_from_file_location("collect", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collect = _charger_collect()

PLAN = "docs/superpowers/plans/2026-10-17-socle-technique.md"
REGISTRE = "docs/superpowers/plans/2026-10-17-socle-technique.progress.md"
PLAN_JSON = [{
    "id": "socle-technique", "title": "Chantier 1 - socle technique", "status": "in_progress",
    "tasksDone": 0, "tasksTotal": 4, "pr": None,
    "planFile": PLAN, "progressFile": REGISTRE,
}]


def _ecrire(repo, rel, texte):
    chemin = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)


def _repo_temp(nb_taches=4):
    """Dépôt minimal (plan + plans.json) dans un dossier temporaire ; rend (dossier, racine)."""
    dossier = tempfile.TemporaryDirectory()
    repo = dossier.name
    _ecrire(repo, PLAN, "".join(f"### Task {n}: Tâche {n}\n" for n in range(1, nb_taches + 1)))
    _ecrire(repo, "docs/dashboard/plans.json", json.dumps(PLAN_JSON))
    return dossier, repo


def _load_sources(repo, projet=None, **kwargs):
    """load_sources() sans aucune lecture en dehors du dossier temporaire : projet, usage DeepSeek et
    server.log DeepSeek pointent vers des fichiers inexistants du dépôt temporaire (jamais le vrai HOME)."""
    return collect.load_sources(
        repo, projet or os.path.join(repo, "pas-de-projet"),
        os.path.join(repo, "pas-d-usage.log"),
        deepseek_log_path=os.path.join(repo, "pas-de-server.log"),
        gh=os.path.join(repo, "gh-introuvable"), git=os.path.join(repo, "git-introuvable"),
        **{"repo_gh": "exemple/depot", **kwargs})


def _sources(repo, **extra):
    """`sources` minimal, sans aucune lecture : ce que load_sources() produirait dans le cas le plus pauvre."""
    sources = {
        "repo_gh": "proprietaire/depot",
        "journal_git_status": "", "transcriptions": [], "usage_texte": "", "deepseek_log": "",
        "plans": [], "registres": {}, "taches_courantes": None, "total_taches": {},
        "runs": [], "prs": [], "worktrees": [], "todo": [], "alerts_sources": [],
    }
    sources.update(extra)
    return sources


def _sources_plan(repo, versionne, sdd=None, **extra):
    """`sources` d'un dépôt avec son plan : titres lus dans le fichier, registres fournis en clair."""
    heads, total = collect.taches_plan(repo, PLAN_JSON)
    registres = {"socle-technique": [t for t in (versionne, sdd) if t]}
    return _sources(repo, plans=json.loads(json.dumps(PLAN_JSON)), registres=registres,
                    taches_courantes=heads, total_taches=total, **extra)


def _etats(board):
    return {t["id"]: t["state"] for t in board["current"]["tasks"]}


class CollectTest(unittest.TestCase):
    def test_progress_ledger_states(self):
        """Registre versionné : complete → done, impl → review, tests → in_progress, absent → todo."""
        dossier, repo = _repo_temp()
        with dossier:
            # Task 1 terminée, Task 2 en implémentation (après ses tests : l'état avance, il ne recule pas),
            # Task 3 aux tests, Task 4 sans ligne
            board = collect.build_board(_sources_plan(
                repo, "Task 1: complete (PR #3)\nTask 2: tests\nTask 2: impl\nTask 3: tests\n"))
        self.assertEqual(_etats(board), {"1": "done", "2": "review", "3": "in_progress", "4": "todo"})
        self.assertEqual(board["plans"][0]["tasksDone"], 1)
        self.assertEqual(board["plans"][0]["tasksTotal"], 4)

    def test_done_counts_only_tasks_of_the_plan(self):
        """Une ligne « Task N: complete » dont le numéro n'est pas un titre du plan ne compte pas (sous-tâches 3a, 3b…)."""
        dossier, repo = _repo_temp()
        with dossier:
            board = collect.build_board(_sources_plan(repo, "Task 1: complete\nTask 5: complete\nTask 6: complete\n"))
        self.assertEqual(board["plans"][0]["tasksDone"], 1)
        self.assertEqual(board["plans"][0]["tasksTotal"], 4)

    def test_output_has_required_keys(self):
        """Le JSON publié contient toutes les clés de l'interface, dont tokens.claudeVsDeepseek."""
        dossier, repo = _repo_temp(nb_taches=2)
        with dossier:
            board = collect.build_board(_sources_plan(repo, ""))
        for key in ("updatedAt", "repo", "plans", "worktrees", "agents", "ci", "prs", "current", "alerts", "todo", "deepseek", "tokens"):
            self.assertIn(key, board)
        for key in ("plan", "tasks"):
            self.assertIn(key, board["current"])
        for key in ("total", "byModel", "byRole", "byDay", "claudeVsDeepseek"):
            self.assertIn(key, board["tokens"])
        for key in ("claude", "deepseek", "deepseekShare"):
            self.assertIn(key, board["tokens"]["claudeVsDeepseek"])
        json.dumps(board)  # sérialisable tel quel sur stdout

    def test_no_message_content_leaks(self):
        """Seuls des compteurs sont lus : ni le texte des transcriptions ni la description d'un agent n'apparaissent."""
        with tempfile.TemporaryDirectory() as repo:
            projet = os.path.join(repo, "projet")
            os.makedirs(projet)
            with open(os.path.join(projet, "session.jsonl"), "w", encoding="utf-8") as f:
                for i in range(2):
                    f.write(json.dumps({
                        "type": "user", "timestamp": "2026-10-17T09:00:00Z",
                        "message": {"role": "user", "content": "SECRET-CONTENU question"},
                    }) + "\n")
                    f.write(json.dumps({
                        "type": "assistant", "timestamp": "2026-10-17T09:00:01Z", "entrypoint": "cli", "requestId": f"r{i}",
                        "message": {"id": f"m{i}", "role": "assistant", "model": "claude-sonnet-4-5-20250929",
                                    "content": [{"type": "text", "text": "SECRET-CONTENU réponse"}],
                                    "usage": {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
                    }) + "\n")
            # sous-agent : sa fiche porte une description libre, qui ne doit jamais être publiée
            with open(os.path.join(projet, "agent-42.meta.json"), "w", encoding="utf-8") as f:
                json.dump({"agentType": "general-purpose", "description": "SECRET-CONTENU mission"}, f)
            with open(os.path.join(projet, "agent-42.jsonl"), "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "assistant", "timestamp": "2026-10-17T09:00:02Z", "requestId": "r-agent",
                    "message": {"id": "m-agent", "model": "claude-sonnet-4-5-20250929", "usage": {"input_tokens": 0, "output_tokens": 0}},
                }) + "\n")
            sources = _load_sources(repo, projet)
            self.assertTrue(any(t.get("isAgent") for t in sources["transcriptions"]))
            board = collect.build_board(sources)

        texte = json.dumps(board, ensure_ascii=False)
        self.assertNotIn("SECRET-CONTENU", texte)
        self.assertEqual(board["tokens"]["total"], 30)  # 2 réponses × (10 entrée + 5 sortie)
        self.assertEqual([a["type"] for a in board["agents"]], ["general-purpose"])
        self.assertNotIn("description", board["agents"][0])

    def test_most_advanced_state_wins_across_ledgers(self):
        """Registre versionné ET registre SDD fusionnés : l'état de rang maximal gagne, dans les deux sens."""
        dossier, repo = _repo_temp(nb_taches=3)
        with dossier:
            board = collect.build_board(_sources_plan(
                repo,
                "Task 2: impl\nTask 3: complete (PR #41)\n",
                "Task 2: complete (commits a..b, review clean, PR #40 → c)\nTask 3: impl\n"))
        taches = {t["id"]: t for t in board["current"]["tasks"]}
        self.assertEqual(taches["2"]["state"], "done")
        self.assertEqual(taches["3"]["state"], "done")
        self.assertEqual(taches["2"]["pr"], 40)
        self.assertEqual(taches["3"]["pr"], 41)

    def test_sdd_ledger_is_found_from_plan_file_name(self):
        """Registre SDD trouvé par le nom du fichier de plan (sans extension), pas par l'identifiant du plan."""
        with tempfile.TemporaryDirectory() as repo:
            _ecrire(repo, PLAN, "### Task 1: A\n### Task 2: B\n")
            _ecrire(repo, "docs/dashboard/plans.json", json.dumps([{
                "id": "socle-technique", "title": "Chantier 1 - socle technique", "status": "in_progress",
                "tasksDone": 0, "tasksTotal": 2, "pr": None,
                "planFile": PLAN, "progressFile": None,
            }]))
            _ecrire(repo, ".superpowers/sdd/2026-10-17-socle-technique/progress.md",
                    "Task 1: complete (commits a..b, review clean, PR #39 → c)\n")
            sources = _load_sources(repo)
            board = collect.build_board(sources)
        taches = {t["id"]: t for t in board["current"]["tasks"]}
        self.assertEqual(taches["1"]["state"], "done")
        self.assertEqual(taches["1"]["pr"], 39)
        self.assertEqual(taches["2"]["state"], "todo")
        self.assertEqual(board["plans"][0]["tasksDone"], 1)

    def test_state_never_regresses(self):
        """« complete » puis « impl » dans le même registre : la tâche reste done."""
        dossier, repo = _repo_temp(nb_taches=2)
        with dossier:
            board = collect.build_board(_sources_plan(repo, "Task 1: complete (PR #3)\nTask 1: impl\n"))
        self.assertEqual(_etats(board)["1"], "done")

    def test_noise_lines_are_ignored(self):
        """fix round, minor (deferred), Ruling, parked : ni changement d'état, ni tâche inventée."""
        dossier, repo = _repo_temp(nb_taches=2)
        with dossier:
            bruit = ("Task 1: fix round 2/5 (tout addressed ; commits a..b)\n"
                     "Task 1: minor (deferred): un détail\n"
                     "Task 1: Ruling: une décision\n"
                     "Task 1: parked (en attente du propriétaire)\n"
                     "Task 7: fix round 1/5 (11 addressed)\n"
                     "Ruling: ligne sans numéro de tâche\n")
            board = collect.build_board(_sources_plan(repo, "Task 1: impl\n", bruit))
        self.assertEqual(_etats(board), {"1": "review", "2": "todo"})  # aucune tâche 7 inventée

    def test_malformed_jsonl_lines_are_skipped(self):
        """Une ligne JSON invalide au milieu d'une transcription ne casse pas le comptage."""
        with tempfile.TemporaryDirectory() as repo:
            projet = os.path.join(repo, "projet")
            os.makedirs(projet)
            with open(os.path.join(projet, "session.jsonl"), "w", encoding="utf-8") as f:
                for i in (1, 2):
                    f.write(json.dumps({
                        "type": "assistant", "timestamp": "2026-10-17T09:00:01Z", "entrypoint": "cli", "requestId": f"r{i}",
                        "message": {"id": f"m{i}", "model": "claude-sonnet-4-5-20250929", "usage": {"input_tokens": 4, "output_tokens": 6}},
                    }) + "\n")
                    f.write("{ceci n'est pas du JSON\n")  # ligne abîmée au milieu
                f.write("[1, 2, 3]\n\"une chaîne\"\n")
            sources = _load_sources(repo, projet)
            board = collect.build_board(sources)
        self.assertEqual(board["tokens"]["total"], 20)  # 2 réponses valides × (4 + 6)
        self.assertEqual(board["tokens"]["requests"], 2)

    def test_gh_unavailable_gives_warn_alert(self):
        """gh introuvable (chemin injecté) : listes vides, une alerte warn en français, aucune alerte bad."""
        with tempfile.TemporaryDirectory() as repo:
            sources = _load_sources(repo)
            self.assertEqual((sources["runs"], sources["prs"]), ([], []))
            board = collect.build_board(sources)
        warn = [a for a in board["alerts"] if a["level"] == "warn"]
        self.assertEqual(len(warn), 2)  # une par appel gh (runs, PR) ; rien d'autre dans ce dépôt vide
        for a in warn:
            self.assertIn("GitHub injoignable", a["text"])
            self.assertIn("listes vides", a["text"])
        # aucun job DeepSeek en échec : rien ne doit être marqué « à traiter »
        self.assertEqual([a for a in board["alerts"] if a["level"] == "bad"], [])

    def test_no_sdd_ledger_without_plan_file(self):
        """Plan sans fichier de plan : aucun registre SDD à chercher (chemin None, pas d'E/S inventée)."""
        self.assertIsNone(collect.registre_sdd({"id": "x"}))


if __name__ == "__main__":
    unittest.main()


class AiTeamCollectTest(unittest.TestCase):
    def test_repo_from_remote(self):
        self.assertEqual(collect.repo_from_remote("https://github.com/a/b.git"), "a/b")
        self.assertEqual(collect.repo_from_remote("git@github.com:a/b.git"), "a/b")
        self.assertEqual(collect.repo_from_remote("https://github.com/a/b"), "a/b")
        self.assertIsNone(collect.repo_from_remote("https://gitlab.com/a/b"))
        self.assertIsNone(collect.repo_from_remote(""))

    def test_slug_for(self):
        self.assertEqual(collect.slug_for("/Users/x/Dev/Orbital"), "-Users-x-Dev-Orbital")
        self.assertEqual(collect.slug_for("/Users/x/.claude"), "-Users-x--claude")

    def test_no_remote_gives_null_repo(self):
        board = collect.build_board({"repo_gh": None})
        self.assertIsNone(board["repo"])
        self.assertTrue(any(a["level"] == "warn" and "GitHub" in a["text"] for a in board["alerts"]))


class DiscoverPlansTest(unittest.TestCase):
    def test_plans_discovered_without_plans_json(self):
        with tempfile.TemporaryDirectory() as repo:
            d = os.path.join(repo, "docs/superpowers/plans")
            os.makedirs(d)
            with open(os.path.join(d, "2026-01-01-x.md"), "w") as f:
                f.write("# Titre X\n\n### Task 1: a\n\n### Task 2: b\n\n### Task 3: c\n")
            plans = _load_sources(repo)["plans"]
        self.assertEqual(len(plans), 1)
        p = plans[0]
        self.assertEqual((p["id"], p["title"], p["tasksTotal"], p["status"]),
                         ("2026-01-01-x", "Titre X", 3, "todo"))
        self.assertEqual(p["planFile"], "docs/superpowers/plans/2026-01-01-x.md")
