# Équipe multi-agents multi-modèles - plan d'implémentation (chantier 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un plugin Claude Code portable (`claude-setup`) qui fournit l'équipe d'agents globale, `/debate`, `/verify`, `/grok`, `/cycle`, et un `bootstrap.sh` pour réinstaller le tout sur une autre machine.

**Architecture:** Repo `~/Dev/claude-setup` = plugin + marketplace locale. Les ponts vers les autres modèles sont des scripts Python stdlib dans `bin/` (`snapshot.py` copie filtrée, `gpt.py` → Codex CLI, `grok.py` → API xAI) appelés par les skills via Bash. Les règles transverses (routage des skills, DeepSeek, confidentialité) vivent dans `rules/team.md`, importé depuis `~/.claude/CLAUDE.md`.

**Tech Stack:** Markdown (agents, skills), Python 3 stdlib + `unittest`, Bash, Codex CLI, API xAI (compatible OpenAI), MCP DeepSeek existant.

**Spec:** `/Users/anthonyguillaume/.claude/docs/superpowers/specs/2026-11-27-multi-agents-design.md`

## Global Constraints

- Aucune installation (Codex, paquets) sans accord explicite d'Anthony au moment de la faire.
- Jamais de `git push` sans accord explicite. Aucune mention de Claude / Claude Code / `Co-Authored-By` dans commits et PR.
- Modifications hors de `~/.claude` et `~/Dev/claude-setup` : accord requis. Lire `~/.agents/` : accord requis.
- Compte GitHub : celui associé à l'adresse perso (pas `anthonyguillaume_getlink`). Repo **privé**.
- Noms de commandes, skills, agents, scripts en **anglais**. Docs et prompts peuvent être en français.
- Python stdlib uniquement (aucune dépendance pip). Tests : `python3 -m unittest discover -s tests`.
- Jamais envoyer à GPT/DeepSeek/Grok : `.env*`, `*.pem`, `*.key`, `id_*`, `*credentials*`, `*secret*`, `GH_TOKEN`, `~/.deepseek-mcp/`, ni fichiers non suivis par git. Jamais afficher la valeur d'une clé.
- Codes de sortie communs aux ponts : `0` OK, `2` mauvaise config (clé/outil absent), `3` modèle indisponible (non connecté, quota, timeout). Message d'erreur sur stderr commençant par `GPT_UNAVAILABLE:` ou `GROK_UNAVAILABLE:`.
- Le cycle s'arrête uniquement sur désaccord Claude/GPT et avant tout push ; revue GPT une fois par branche ; GPT indisponible → continuer avec Claude seul et le signaler.
- Traces : `<projet>/.superpowers/debates/AAAA-MM-JJ-<sujet>.md` et `<projet>/.superpowers/progress.md` (non versionnés).

## Review Focus

1. **Projet qui n'est pas un repo git** → `snapshot.py` refuse (exit 2, message clair) au lieu de copier tout le dossier ; le débat continue côté Claude et le signale. Test : `test_snapshot_refuses_non_git_dir` (Task 2).
2. **`.env` ou clé commitée par erreur** → exclue de la copie malgré `git ls-files`. Test : `test_snapshot_excludes_tracked_secrets` (Task 2).
3. **Lien symbolique suivi par git qui pointe hors du repo** (ex. `~/.ssh`) → copié comme lien non résolu ou ignoré, jamais son contenu. Test : `test_snapshot_does_not_follow_symlinks` (Task 2).
4. **Codex non connecté, quota épuisé ou trop lent** → `gpt.py` sort en 3 avec `GPT_UNAVAILABLE:` sans planter le cycle. Tests : `test_gpt_unavailable_on_codex_error`, `test_gpt_timeout` (Task 3).
5. **`XAI_API_KEY` absente ou erreur HTTP** → `grok.py` sort en 2/3 sans jamais imprimer la clé. Tests : `test_grok_missing_key`, `test_grok_http_error_hides_key` (Task 4).

---

## File Structure

```
~/Dev/claude-setup/
  .claude-plugin/plugin.json        # manifeste du plugin "claude-setup"
  .claude-plugin/marketplace.json   # marketplace locale/GitHub listant le plugin
  agents/*.md                       # 12 agents (Task 7)
  skills/debate/SKILL.md            # Task 5
  skills/verify/SKILL.md            # Task 5
  skills/grok/SKILL.md              # Task 6
  skills/cycle/SKILL.md             # Task 9
  skills/delegate-to-deepseek/SKILL.md  # migré + règle faible contexte (Task 8)
  bin/snapshot.py  bin/gpt.py  bin/grok.py
  rules/team.md                     # routage skills + DeepSeek + confidentialité (Task 7)
  manifest/plugins.txt  manifest/skills.txt  manifest/third-party-skills.txt
  bootstrap.sh                      # Task 10
  docs/spec.md  docs/plan.md        # copies de la spec et du plan
  tests/test_layout.py test_snapshot.py test_gpt.py test_grok.py test_agents.py
  .gitignore
```

---

### Task 1: Squelette du repo et du plugin

**Files:**
- Create: `~/Dev/claude-setup/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.gitignore`, `docs/spec.md`, `docs/plan.md`, `manifest/skills.txt`
- Test: `tests/test_layout.py`

**Interfaces:**
- Produces: nom de plugin `claude-setup`, marketplace `claude-setup` ; `manifest/skills.txt` = un nom de skill disponible par ligne (référence pour Task 7).

- [ ] **Step 1:** `mkdir -p ~/Dev/claude-setup && cd ~/Dev/claude-setup && git init` (dossier approuvé par Anthony).
- [ ] **Step 2: Test qui échoue** - `tests/test_layout.py` : `test_plugin_manifest` (JSON valide, `name == "claude-setup"`, champs `version`, `description`) ; `test_marketplace_lists_plugin` (`plugins[0].name == "claude-setup"`, `source == "./"`).
- [ ] **Step 3:** `python3 -m unittest tests.test_layout -v` → FAIL (fichiers absents).
- [ ] **Step 4:** Créer les deux JSON selon le format plugin/marketplace de Claude Code (vérifier le schéma avec l'agent `claude-code-guide` si doute). `.gitignore` : `__pycache__/`, `.superpowers/`, `*.log`. Copier spec et plan dans `docs/`. Remplir `manifest/skills.txt` avec la liste des skills de la section « Skills » de la spec (noms exacts, plugins préfixés `plugin:skill`).
- [ ] **Step 5:** Tests → PASS.
- [ ] **Step 6:** `claude plugin marketplace add ~/Dev/claude-setup` puis `claude plugin install claude-setup@claude-setup`. Vérifier `claude plugin list` → `claude-setup` présent.
- [ ] **Step 7:** Commit `chore: scaffold claude-setup plugin`.

### Task 2: `snapshot.py` - copie filtrée du projet

**Files:**
- Create: `bin/snapshot.py`
- Test: `tests/test_snapshot.py`

**Interfaces:**
- Produces: CLI `python3 bin/snapshot.py <project_dir>` → imprime sur stdout le chemin d'un dossier temporaire contenant la copie filtrée ; exit 2 si `<project_dir>` n'est pas un repo git. Fonction `make_snapshot(project_dir: str) -> str`, constante `EXCLUDE_PATTERNS: list[str]`.

- [ ] **Step 1: Tests qui échouent** (chaque test crée un repo git temporaire avec `git init` + fichiers + `git add`) :
  - `test_snapshot_copies_tracked_files` : `src/a.py` présent dans la copie.
  - `test_snapshot_skips_untracked` : fichier non ajouté absent.
  - `test_snapshot_excludes_tracked_secrets` : `.env`, `.env.local`, `deploy.pem`, `id_rsa`, `aws_credentials.json`, `my_secret.txt` suivis par git → tous absents.
  - `test_snapshot_respects_aiignore` : `.aiignore` contenant `private/` → `private/x.md` absent.
  - `test_snapshot_does_not_follow_symlinks` : lien suivi `link -> /etc` → la copie ne contient pas le contenu de `/etc`.
  - `test_snapshot_refuses_non_git_dir` : CLI sur dossier non git → exit 2, stderr contient `not a git repository`.
- [ ] **Step 2:** `python3 -m unittest tests.test_snapshot -v` → FAIL.
- [ ] **Step 3:** Implémenter `make_snapshot` : `git -C dir ls-files -z`, filtre `fnmatch` sur le nom et le chemin (`EXCLUDE_PATTERNS = [".env*", "*.pem", "*.key", "id_*", "*credentials*", "*secret*"]` + lignes de `.aiignore`), copie avec `shutil.copy2(..., follow_symlinks=False)`, destination `tempfile.mkdtemp(prefix="ai-snapshot-")`.
- [ ] **Step 4:** Tests → PASS.
- [ ] **Step 5:** Commit `feat: filtered project snapshot for external models`.

### Task 3: Codex CLI et `gpt.py`

**Files:**
- Create: `bin/gpt.py`
- Test: `tests/test_gpt.py`

**Interfaces:**
- Consumes: `snapshot.make_snapshot`.
- Produces: CLI `python3 bin/gpt.py [--project DIR] [--resume SESSION_ID] [--timeout 600] < prompt.txt` → stdout = dernière réponse de GPT ; stderr dernière ligne = `SESSION: <id>` ; exit 0/2/3 (Global Constraints). Sans `--project`, Codex tourne dans un dossier temporaire vide.

- [ ] **Step 1: Installer Codex - DEMANDER L'ACCORD d'Anthony d'abord.** Proposer `brew install codex` (ou `npm i -g @openai/codex`). Puis Anthony lance `! codex login` (compte ChatGPT Plus). Vérifier : `codex exec --help` et noter les flags réels pour `--sandbox read-only`, `-C/--cd`, `--json`, `--output-last-message`, `--skip-git-repo-check`, et `codex exec resume`. Adapter les étapes suivantes aux flags constatés.
- [ ] **Step 2: Tests qui échouent** - un faux `codex` (script shell dans un dossier temporaire mis en tête de `PATH`) simule les cas :
  - `test_gpt_returns_answer` : faux codex écrit `réponse` dans le fichier de sortie et un id de session → stdout `réponse`, stderr contient `SESSION: abc`.
  - `test_gpt_runs_read_only_in_snapshot` : le faux codex enregistre ses arguments → contiennent `read-only` et le chemin du snapshot, jamais le dossier du projet d'origine.
  - `test_gpt_resume_passes_session` : `--resume abc` → arguments contiennent `resume` et `abc`.
  - `test_gpt_missing_codex` : `PATH` sans codex → exit 2, `GPT_UNAVAILABLE: codex not installed`.
  - `test_gpt_unavailable_on_codex_error` : faux codex sort en 1 avec « not logged in » → exit 3, `GPT_UNAVAILABLE:`.
  - `test_gpt_timeout` : faux codex `sleep 5`, `--timeout 1` → exit 3, `GPT_UNAVAILABLE: timeout`.
- [ ] **Step 3:** Tests → FAIL.
- [ ] **Step 4:** Implémenter `gpt.py` : `subprocess.run([... codex exec ...], timeout=...)`, snapshot si `--project`, lecture de la dernière réponse via `--output-last-message`, extraction de l'id de session depuis la sortie `--json`.
- [ ] **Step 5:** Tests → PASS.
- [ ] **Step 6: Essai réel** : `echo "Réponds juste OK" | python3 bin/gpt.py` → stdout contient `OK`, exit 0.
- [ ] **Step 7:** Commit `feat: GPT bridge through Codex CLI`.

### Task 4: `grok.py` - pont xAI

**Files:**
- Create: `bin/grok.py`
- Test: `tests/test_grok.py`

**Interfaces:**
- Produces: CLI `python3 bin/grok.py [--model M] [--timeout 300] < prompt.txt` → stdout = réponse. Lit `XAI_API_KEY` (obligatoire), `XAI_BASE_URL` (défaut `https://api.x.ai/v1`), `XAI_MODEL` (défaut : à fixer d'après la doc xAI au moment de l'implémentation, consigné dans `rules/team.md`). Ne lit aucun fichier du projet.

- [ ] **Step 1: Tests qui échouent** - un `http.server` local dans un thread sert de faux xAI (`XAI_BASE_URL=http://127.0.0.1:<port>/v1`) :
  - `test_grok_returns_answer` : réponse `{"choices":[{"message":{"content":"salut"}}]}` → stdout `salut` ; la requête reçue a l'en-tête `Authorization: Bearer test-key` et le prompt dans `messages`.
  - `test_grok_missing_key` : pas de `XAI_API_KEY` → exit 2, `GROK_UNAVAILABLE: XAI_API_KEY not set`.
  - `test_grok_http_error_hides_key` : serveur renvoie 429 → exit 3, stderr contient `GROK_UNAVAILABLE: HTTP 429` et **ne contient pas** `test-key`.
- [ ] **Step 2:** Tests → FAIL.
- [ ] **Step 3:** Implémenter avec `urllib.request` (POST `<base>/chat/completions`).
- [ ] **Step 4:** Tests → PASS.
- [ ] **Step 5:** Commit `feat: Grok bridge through xAI API`. (Essai réel reporté jusqu'à ce qu'Anthony ait créé sa clé.)

### Task 5: Skills `/debate` et `/verify`

**Files:**
- Create: `skills/debate/SKILL.md`, `skills/verify/SKILL.md`

**Interfaces:**
- Consumes: `bin/gpt.py` (chemin via `${CLAUDE_PLUGIN_ROOT}/bin/gpt.py` ; vérifier que la variable est disponible dans les skills de plugin, sinon chemin absolu écrit par `bootstrap.sh`).
- Produces: `/debate <question>` et `/verify` ; fichier de synthèse `<projet>/.superpowers/debates/AAAA-MM-JJ-<sujet>.md` dont la première ligne est `RESULT: AGREEMENT` ou `RESULT: DISAGREEMENT` (lu par `/cycle`, Task 9).

- [ ] **Step 1:** `debate/SKILL.md` - frontmatter `name: debate`, description en anglais qui déclenche sur « debate », « second opinion », « challenge this decision ». Corps = protocole de la spec §2 :
  - Tour 0 en aveugle : sous-agent Claude (Opus) et `gpt.py --project <projet>` reçoivent le **même** brief ; format imposé `POSITION / ARGUMENTS / CONFIDENCE (0-100) / WHAT WOULD CHANGE MY MIND`.
  - Tours 1 et 2 : chacun reçoit l'autre réponse ; format `CONCEDE / CONTEST / REVISED POSITION` ; consigne « ne concède que ce que tu peux justifier ». Tour 2 seulement si désaccord. GPT reprend sa session via `--resume`.
  - Synthèse : `RESULT:` + tableau accords / divergences avec les meilleurs arguments de chaque côté ; l'orchestrateur ne tranche pas.
  - `gpt.py` exit 2/3 → synthèse marquée `RESULT: AGREEMENT (CLAUDE ONLY - GPT unavailable: <raison>)` et le dire à Anthony.
- [ ] **Step 2:** `verify/SKILL.md` - `name: verify`, lancé à la main. Envoie à `gpt.py` la dernière réponse/production de Claude + le contexte utile ; consigne à GPT : chercher erreurs factuelles, API ou fichiers inventés, raisonnement faux, avec preuve. Claude répond point par point (accepte/réfute avec preuve). Désaccord restant → proposer `/debate`.
- [ ] **Step 3: Essai manuel** (dans un projet git de test) : `/verify` après une affirmation volontairement fausse (« `Array.prototype.flat` modifie le tableau d'origine ») → GPT la conteste, Claude reconnaît. `/debate "SQLite ou PostgreSQL pour une appli mono-utilisateur locale ?"` → fichier de synthèse créé avec ligne `RESULT:`.
- [ ] **Step 4:** Vérifier que `/debate` et `/verify` fonctionnent sans préfixe ; sinon noter dans `rules/team.md` la forme `/claude-setup:debate`.
- [ ] **Step 5:** Commit `feat: debate and verify skills`.

### Task 6: Skill `/grok`

**Files:**
- Create: `skills/grok/SKILL.md`

**Interfaces:**
- Consumes: `bin/grok.py`.

- [ ] **Step 1:** `name: grok`, **`disable-model-invocation: true`** (appel explicite uniquement, spec §Grok). Corps : usages visés (fiction sombre, satire, humour cru, visuels refusés par excès de prudence, tendances X) ; n'envoyer que le texte du prompt, jamais de fichiers ni de secrets ; afficher la réponse brute en la signalant comme venant de Grok ; ne pas servir de relais automatique quand Claude refuse.
- [ ] **Step 2:** Essai manuel une fois `XAI_API_KEY` en place : `/grok Écris une blague cynique sur les réunions` → réponse affichée ; sans clé → message `GROK_UNAVAILABLE` relayé.
- [ ] **Step 3:** Commit `feat: grok skill`.

### Task 7: Agents et `rules/team.md`

**Files:**
- Create: `agents/challenger.md`, `product-owner.md`, `front-react.md`, `back-csharp.md`, `back-node.md`, `back-rust.md`, `test-writer.md`, `reviewer.md`, `security.md`, `qa.md`, `doc-writer.md` ; `rules/team.md`
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: `manifest/skills.txt` (Task 1).
- Produces: agents nommés comme les fichiers ; verdicts du `reviewer` et du `security` au format `VERDICT: APPROVE` / `VERDICT: REQUEST_CHANGES` + liste de points (format Orbital).

- [ ] **Step 1: Test qui échoue** - `tests/test_agents.py` :
  - `test_agents_frontmatter` : chaque `agents/*.md` a `name` (= nom du fichier), `description`, `model` ∈ {`fable`,`opus`,`sonnet`,`haiku`}.
  - `test_agents_models_match_spec` : `back-rust`, `reviewer`, `security` → `opus` ; `product-owner` → `fable` ; les autres → `sonnet`.
  - `test_agents_skills_exist` : chaque entrée `skills:` figure dans `manifest/skills.txt`.
  - `test_readonly_agents` : `reviewer`, `security` n'ont ni `Edit` ni `Write` dans `tools`.
- [ ] **Step 2:** Tests → FAIL.
- [ ] **Step 3:** Écrire les agents d'après la table §3 et la table « Skills » de la spec (skills préchargés via `skills:`). S'inspirer des corps d'agents d'Orbital (`/Users/anthonyguillaume/Dev/Orbital/rules/agents/*.md`, lecture autorisée). `challenger` : appelle `gpt.py` et renvoie la réponse brute sans la reformuler. `doc-writer` : délègue la rédaction à DeepSeek flash puis relit.
- [ ] **Step 4:** `rules/team.md` : table de routage des skills (copie de la spec), règles DeepSeek (DS-02 jamais délégué : auth, isolation des données, audit, crypto, architecture, revue finale ; faible contexte uniquement ; vérification + `acknowledge_deepseek_mutations`), règles de confidentialité, quand proposer `/debate` / `/verify`, et rappel que les agents d'un projet priment sur les globaux.
- [ ] **Step 5:** Tests → PASS.
- [ ] **Step 6:** Commit `feat: global agent team and team rules`.

### Task 8: Migrer `delegate-to-deepseek`

**Files:**
- Create: `skills/delegate-to-deepseek/SKILL.md` (copie de `~/.claude/skills/delegate-to-deepseek/SKILL.md`, puis modifiée)
- Delete (après accord) : `~/.claude/skills/delegate-to-deepseek/`

- [ ] **Step 1:** Copier la skill dans le repo. Remplacer la règle « 中等及以下 » (moyen et moins) par : tâches **à faible contexte** uniquement (traductions, CRUD isolé, docs, résumés de tests, scans en lecture seule) ; ajouter la liste DS-02 ; renvoyer vers `rules/team.md`. Garder le reste du protocole (vérification, recovery).
- [ ] **Step 2:** Demander à Anthony l'accord pour supprimer l'ancienne copie dans `~/.claude/skills/` (sinon doublon de nom). Supprimer.
- [ ] **Step 3:** Vérifier dans une nouvelle session que la skill listée est celle du plugin (description mentionne « low-context »).
- [ ] **Step 4:** Commit `feat: delegate-to-deepseek limited to low-context work`.

### Task 9: Skill `/cycle`

**Files:**
- Create: `skills/cycle/SKILL.md`

**Interfaces:**
- Consumes: `/debate` (ligne `RESULT:`), agents de Task 7, `rules/team.md`.

- [ ] **Step 1:** `name: cycle`. Au démarrage, si le modèle de la session n'est pas Fable (orchestrateur de la spec §3), le dire et proposer `/model fable` sans bloquer. Corps = cycle de la spec §4, en s'appuyant sur superpowers au lieu de le refaire :
  1. `superpowers:brainstorming` avec Anthony (+ `product-owner`), puis `/debate` sur la spec ; Anthony valide la spec.
  2. `superpowers:writing-plans`, puis `/debate` sur le plan. `AGREEMENT` → continuer sans arrêt et choisir l'exécution subagent-driven ; `DISAGREEMENT` → arrêt, présenter la synthèse.
  3. `superpowers:subagent-driven-development` avec les agents du projet s'ils existent (`.claude/agents/`), sinon les globaux ; mécanique → DeepSeek selon `rules/team.md`.
  4. Fin de branche : revue `reviewer` en parallèle de revue GPT (`gpt.py --project`, même consigne et format `VERDICT:`) sur le diff complet ; `security` si chemins sensibles ; `qa` si UI. Verdicts identiques → continuer ; différents → `/debate` 2 tours → toujours différents → arrêt. 2 `REQUEST_CHANGES` concordants consécutifs → arrêt.
  5. Fusion locale, puis **arrêt systématique avant push**.
  - Journal `.superpowers/progress.md` : une ligne `Décision : … - coût si faux : …` par accord automatique ; `GPT unavailable` noté quand c'est le cas.
- [ ] **Step 2: Essai bout en bout** sur un petit projet jetable (ex. `~/Dev/claude-setup-sandbox`, accord requis pour le créer) : « une CLI Node qui compte les mots d'un fichier ». Attendu : arrêt après validation de la spec seulement si désaccord, `progress.md` rempli, revue double tracée, arrêt avant push.
- [ ] **Step 3:** Commit `feat: cycle skill orchestrating the multi-model workflow`.

### Task 10: `bootstrap.sh` et manifestes de portabilité

**Files:**
- Create: `bootstrap.sh`, `manifest/plugins.txt`, `manifest/third-party-skills.txt`
- Modify: `~/.claude/CLAUDE.md` (ajout d'une ligne `@~/Dev/claude-setup/rules/team.md`)

**Interfaces:**
- Produces: `./bootstrap.sh --check` (n'installe rien, affiche un état `OK`/`MISSING` par élément, exit 1 si quelque chose manque) et `./bootstrap.sh` (installe, en demandant `[y/N]` avant chaque installation).

- [ ] **Step 1:** `manifest/plugins.txt` : un `plugin@marketplace` par ligne + les marketplaces tierces (`ui-ux-pro-max-skill`, `ponytail`, `context-mode`, `handoff-marketplace`) avec leur repo GitHub, depuis `~/.claude/settings.json`.
- [ ] **Step 2:** `manifest/third-party-skills.txt` : origine de chaque skill tierce. **Demander l'accord** pour lire `~/.agents/` (fichier de verrou de l'outil `skills`) afin de retrouver les sources ; pour les dossiers copiés sans origine connue, les marquer `unknown` et le signaler à Anthony.
- [ ] **Step 3:** `bootstrap.sh --check` vérifie : `claude`, `codex` (+ `codex login status`), plugins du manifeste, plugin `claude-setup`, serveur MCP `deepseek` (`claude mcp list`), `XAI_API_KEY` définie (sans valeur), `COMFYUI_URL`, ligne d'import dans `~/.claude/CLAUDE.md`.
- [ ] **Step 4:** Mode installation : pour chaque `MISSING`, proposer la commande et demander `[y/N]`. Serveur DeepSeek : cloner/installer depuis son repo d'origine (à identifier dans `~/Dev/mcp/deepseek-as-subagent/.git/config`, lecture autorisée par accord), puis `claude mcp add`.
- [ ] **Step 5:** Vérifier `./bootstrap.sh --check` sur cette machine → tout `OK` sauf `XAI_API_KEY` si pas encore créée.
- [ ] **Step 6:** Ajouter l'import dans `~/.claude/CLAUDE.md` ; vérifier dans une nouvelle session que les règles de `team.md` sont chargées (`/memory`).
- [ ] **Step 7:** Commit `feat: bootstrap script and portability manifests`.

### Task 11: Publication sur GitHub

- [ ] **Step 1:** `gh auth status` → compte perso actif. **Demander l'accord** pour créer le repo privé et pousser.
- [ ] **Step 2:** `gh repo create claude-setup --private --source . --push`.
- [ ] **Step 3:** Créer `README.md` (section « Nouvelle machine » : `claude plugin marketplace add <compte>/claude-setup`, `claude plugin install claude-setup@claude-setup`, `./bootstrap.sh`). Commit + push (accord déjà donné à l'étape 1 pour ce repo, le redemander si autre chose que ce commit).
