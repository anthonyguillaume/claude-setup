# /dashboard - plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Une commande `/dashboard` qui crée puis met à jour un tableau de suivi (artifact claude.ai privé) par projet, à partir d'un collecteur commun repris d'Orbital.

**Architecture:** `bin/dashboard_collect.py` (stdlib, `build_board` pur + `load_sources` pour les E/S) produit le JSON `board/latest`. `dashboard/dashboard.html` le lit dans la base de l'artifact. La skill `/dashboard` publie la page une fois par projet (adresse dans `docs/dashboard/config.json`) puis écrit les chiffres avec `ArtifactData`.

**Tech Stack:** Python 3 stdlib + unittest, HTML/JS (base de l'artifact), outils Artifact et ArtifactData.

**Spec:** `docs/dashboard-spec.md`

## Global Constraints

- Tableaux d'Orbital, OrbitalInvest, bowtrail inchangés (lecture seule de leurs fichiers).
- Compteurs seulement : jamais de contenu d'échange, de secrets, de données personnelles. Aucun chiffre inventé.
- Écriture de la base réservée au propriétaire (`owner`), lecture `view`.
- `gh` avec `GH_TOKEN=$(gh auth token -u <compte>)` ; compte : `anthonyguillaume_getlink` si le projet est sous un dossier `Eurotunnel`, sinon `anthonyguillaume`.
- Pas de tiret cadratin, point médian ni emoji (y compris dans la page reprise d'Orbital).
- Tests : `python3 -m unittest discover -s tests`.

## Review Focus

1. **Projet sans remote GitHub** (repo local seul) : `repo` vaut `null`, PR et CI vides, une alerte `warn`, pas de plantage. Test : `test_no_remote_gives_null_repo` (Task 1).
2. **Projet sans `docs/dashboard/plans.json`** : plans déduits de `docs/superpowers/plans/*.md`. Test : `test_plans_discovered_without_plans_json` (Task 2).
3. **`usage.log` absent ou avec lignes corrompues** : compteurs à zéro, lignes invalides ignorées. Test : `test_usage_log_bad_lines_ignored` (Task 4).
4. **Débat sans ligne `RESULT:`** (fichier en cours d'écriture) : compté `unknown`, pas d'erreur. Test : `test_debate_without_result_is_unknown` (Task 4).
5. **Le log d'usage ne contient jamais le prompt ni la réponse.** Test : `test_usage_log_has_no_content` (Task 3).

---

### Task 1: Collecteur commun

**Files:**
- Create: `bin/dashboard_collect.py` (copie de `~/Dev/Orbital/scripts/dashboard/collect.py`), `tests/test_dashboard_collect.py` (copie de `test_collect.py`, chargement adapté au nouveau chemin)

**Interfaces:**
- Produces: `build_board(sources: dict) -> dict` (inchangé, clés d'Orbital) ; `repo_from_remote(url: str) -> str | None` ; `slug_for(path: str) -> str` ; CLI `dashboard_collect.py [--root DIR]` (défaut : cwd), `--repo` et `--project-slug` deviennent optionnels et calculés.

- [ ] **Step 1:** Copier collect.py et test_collect.py ; remplacer `REPO_DEFAUT`/`SLUG_DEFAUT` en dur. Lancer les tests portés : ils doivent passer tels quels (preuve que la copie est fidèle).
- [ ] **Step 2: Tests qui échouent :**
  - `test_repo_from_remote` : `https://github.com/a/b.git` → `a/b` ; `git@github.com:a/b.git` → `a/b` ; `https://gitlab.com/a/b` → `None`.
  - `test_slug_for` : `/Users/x/Dev/Orbital` → `-Users-x-Dev-Orbital` ; `/Users/x/.claude` → `-Users-x--claude` (tout caractère non alphanumérique devient `-`).
  - `test_no_remote_gives_null_repo` : `build_board` avec `repo_gh=None` → `board["repo"] is None`, alerte `warn` contenant `GitHub`.
- [ ] **Step 3:** Implémenter ; `load_sources` ne lance pas `gh` quand `repo_gh` est `None`.
- [ ] **Step 4:** Remplacer dans les deux fichiers les tirets cadratins et points médians par `-`. Tests verts.
- [ ] **Step 5:** Commit `feat: shared dashboard collector`.

### Task 2: Plans découverts automatiquement

**Files:** Modify `bin/dashboard_collect.py` ; Test `tests/test_dashboard_collect.py`

**Interfaces:**
- Produces: `discover_plans(repo: str) -> list[dict]` (mêmes clés que `plans.json` : `id`, `title`, `status`, `tasksDone`, `tasksTotal`, `pr`, `planFile`, `progressFile`).

- [ ] **Step 1: Test qui échoue** `test_plans_discovered_without_plans_json` : dossier avec `docs/superpowers/plans/2026-01-01-x.md` (`# Titre X` + 3 `### Task N:`) sans `plans.json` → un plan `id="2026-01-01-x"`, `title="Titre X"`, `tasksTotal=3`, `status="todo"`, `planFile` relatif.
- [ ] **Step 2:** Implémenter ; `load_sources` l'utilise seulement si `plans.json` est absent ou vide. L'avancement existant (registres SDD) remplit ensuite `tasksDone`.
- [ ] **Step 3:** Tests verts, commit `feat: discover plans when plans.json is missing`.

### Task 3: Journal d'usage GPT et Grok

**Files:** Create `bin/usage_log.py` ; Modify `bin/gpt.py`, `bin/grok.py` ; Test `tests/test_usage_log.py`

**Interfaces:**
- Produces: `record(model: str, project: str | None, ok: bool, seconds: float, tokens: int | None) -> None` qui ajoute une ligne JSON `{"at", "model", "project", "ok", "seconds", "tokens"}` à `AI_TEAM_USAGE_LOG` (défaut `~/.ai-team/usage.log`), sans jamais lever (journal optionnel).

- [ ] **Step 1: Tests qui échouent :** `test_record_appends_json_line` ; `test_usage_log_has_no_content` (gpt.py avec le faux codex et un prompt `SECRET-PROMPT`, réponse `SECRET-ANSWER` → aucune des deux chaînes dans le log, une ligne `model="gpt"`, `ok=true`) ; `test_failed_call_logged_not_ok` (faux codex exit 1 → `ok=false`).
- [ ] **Step 2:** Implémenter ; `gpt.py` lit les tokens dans l'événement `--json` qui porte `usage` (vérifier le nom réel avec un vrai appel : `turn.completed` attendu) ; `project` = racine git de `--project` ou `None`. `grok.py` lit `usage.total_tokens` de la réponse xAI.
- [ ] **Step 3:** Tests verts, commit `feat: usage counters for GPT and Grok calls`.

### Task 4: Modèles et débats dans le tableau

**Files:** Modify `bin/dashboard_collect.py` ; Test `tests/test_dashboard_collect.py`

**Interfaces:**
- Consumes: format de `usage.log` (Task 3), première ligne `RESULT:` des débats.
- Produces: clés `board["models"] = {"claude": {"tokens"}, "gpt": {"calls", "failed", "tokens"}, "grok": {"calls", "failed", "tokens"}, "deepseek": {"tokens"}}` et `board["debates"] = {"total", "agreement", "disagreement", "claudeOnly", "unknown", "recent": [{"date", "topic", "result"}]}` (10 plus récents ; `topic` = nom de fichier sans date ni extension).

- [ ] **Step 1: Tests qui échouent :** `test_models_counts_by_project` (lignes d'autres projets ignorées) ; `test_usage_log_bad_lines_ignored` ; `test_debates_counted` (AGREEMENT, DISAGREEMENT, `AGREEMENT (CLAUDE ONLY ...)`) ; `test_debate_without_result_is_unknown` ; `test_debates_never_include_content` (le corps du débat n'apparaît pas dans le JSON).
- [ ] **Step 2:** Implémenter dans `build_board` (sources `usage_ai_team` et `debates` ajoutées par `load_sources`).
- [ ] **Step 3:** Tests verts, commit `feat: models and debates on the dashboard`.

### Task 4b: Agents en direct et étape du cycle

**Files:** Modify `bin/dashboard_collect.py`, `skills/cycle/SKILL.md` ; Test `tests/test_dashboard_collect.py`

**Interfaces:**
- Produces: chaque entrée de `board["agents"]` gagne `"task"` (description tronquée à 60 caractères ou `None`) et `"lastTool"` (nom du dernier `tool_use` de la transcription ou `None`) ; `"status"` vient de `finished` dans la fiche quand il existe. Nouvelle clé `board["cycle"] = {"phase", "task", "updatedAt"}` lue dans `.superpowers/cycle.json`, ou `None`.
- Consumes (Task 6 et 7) : `PHASES = ["idea", "spec", "plan", "tests", "build", "review", "merge", "push"]`.

- [ ] **Step 1: Tests qui échouent :** `test_agent_task_label_truncated` (description de 80 caractères → 60) ; `test_agent_last_tool_name_only` (transcription avec un `tool_use` `Edit` dont l'argument contient `SECRET-ARG` → `lastTool == "Edit"`, `SECRET-ARG` absent du JSON) ; `test_agent_status_from_meta_finished` ; `test_cycle_phase_read` ; `test_cycle_phase_invalid_is_none` (phase hors liste ou JSON cassé → `None`).
- [ ] **Step 2:** Implémenter. Dans `skills/cycle/SKILL.md`, ajouter : écrire `.superpowers/cycle.json` à chaque changement d'étape, avec une phase de `PHASES`.
- [ ] **Step 3:** Tests verts, commit `feat: live agents and cycle phase on the dashboard`.

### Task 5: Page du tableau

**Files:** Create `dashboard/dashboard.html` (repris de `~/Dev/Orbital/docs/dashboard/dashboard.html`)

- [ ] **Step 1:** Copier la page ; retirer ce qui est propre à Orbital (titre, textes) ; titre `Suivi - <repo>` lu dans `board.repo`.
- [ ] **Step 2a:** Ajouter en tête la **carte animée du cycle** (SVG inline) : les 8 phases de `PHASES` en chemin, revue Claude et GPT côte à côte, l'étape `board.cycle.phase` en surbrillance, flux animé vers l'étape suivante, puces des agents actifs posées sur leur étape (type, modèle, libellé `task`, `lastTool`), badges des débats sur spec, plan et revue (accord vert, désaccord orange). Correspondance agent vers étape : `test-writer` → tests, agents `front-*`/`back-*`/`doc-writer` → build, `reviewer`/`security`/`qa`/`challenger` → review, `product-owner` → idea, autres → étape courante. `prefers-reduced-motion` : aucune animation. Charger la skill `artifact-diagramming` avant d'écrire le SVG.
- [ ] **Step 2:** Ajouter les sections « Modèles » (part des tokens Claude / GPT / DeepSeek / Grok, appels et échecs GPT et Grok) et « Débats » (compteurs + 10 derniers).
- [ ] **Step 3:** Remplacer tirets cadratins et points médians. Vérifier : `grep -c` des caractères interdits = 0 ; ouvrir la page en local avec un `board/latest` factice (Playwright) : aucune erreur console, sections visibles.
- [ ] **Step 4:** Commit `feat: shared dashboard page`.

### Task 6: Skill `/dashboard`

**Files:** Create `skills/dashboard/SKILL.md`

- [ ] **Step 1:** Charger la skill `artifact-capabilities` pour la déclaration exacte de la base (`db`) et des règles d'accès (`board/*`, `events/*` : lecture `view`, écriture `owner`).
- [ ] **Step 2:** Écrire la skill :
  1. Racine du projet = racine git du cwd. Compte `gh` selon les Global Constraints.
  2. `GH_TOKEN=... python3 <base>/../../bin/dashboard_collect.py --root <racine> > <scratchpad>/board.json`.
  3. Si `docs/dashboard/config.json` n'existe pas : copier `dashboard/dashboard.html` dans le scratchpad, publier avec l'outil Artifact (icône `chart`, capacités `db` et règles d'accès), écrire `{"artifact": "<url>"}` dans `docs/dashboard/config.json` et le signaler (fichier à committer). Sinon : ne pas republier, sauf si la page d'ai-team a changé de version (champ `pageVersion` dans config.json).
  4. `ArtifactData` batch : `set board/latest` depuis board.json, `set events/<horodatage>-<sujet>` si un sujet est donné (`/dashboard <sujet>`).
  5. Ouvrir l'artifact.
- [ ] **Step 3: Essai réel** sur `~/Dev/claude-setup` : artifact créé, config.json écrit, chiffres affichés (plans du repo, tokens, débats à 0), second lancement sans republication.
- [ ] **Step 4:** Commit `feat: dashboard skill`.

### Task 7: Rafraîchissement par `/cycle`, docs

**Files:** Modify `skills/cycle/SKILL.md`, `rules/team.md`, `README.md`

- [ ] **Step 1:** `/cycle` : lancer `/dashboard <étape>` en fin de chaque tâche, à chaque porte (spec, plan, revue) et en fin de cycle ; ignorer en silence si l'artifact n'existe pas encore (le premier `/dashboard` le crée).
- [ ] **Step 2:** `rules/team.md` section 6 et README : ajouter `/dashboard`.
- [ ] **Step 3:** Tests verts (dont caractères interdits), commit `docs: dashboard command`, push (compte `anthonyguillaume`).
