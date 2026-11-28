# Règles de développement génériques - design

Cycle 1 sur 3 du chantier « règles, design, nouveau projet ». Cycle 2 : agent `design` et templates de maquettes. Cycle 3 : skills `new-project` et `wrap`.

## Intention

Les projets d'Anthony (Orbital, OrbitalInvest, bowtrail) ont des règles de développement écrites dans `rules/`, recopiées et divergentes d'un projet à l'autre. Les agents d'ai-team n'en ont qu'une ligne ou deux chacun. But : une seule source de règles génériques dans le plugin, chargée par chaque agent selon son rôle, que les projets n'ont plus à recopier.

Succès : un agent ai-team lancé dans un projet sans `rules/` reçoit les règles de son rôle sans lire de fichier hors du dossier de lancement, et les applique.

## Sources

- `/Users/anthonyguillaume/Dev/Orbital/rules/` (source principale), `/Users/anthonyguillaume/Dev/OrbitalInvest/rules/`, `/Users/anthonyguillaume/Dev/bowtrail/rules/`. Lecture seule, déjà autorisée par Anthony le 2026-11-28.
- Le contenu retenu est fixé par l'annexe `2026-11-28-dev-rules-inventory.md` : une ligne par règle (identifiant final, source, comportement). Le constructeur rédige chaque règle à partir de sa source et de cette ligne ; il n'ajoute ni ne retire de règle.

## Objectifs

1. **Règles livrées comme skills du plugin.** Un skill par thème dans `skills/rules-<thème>/SKILL.md` : `rules-index`, `rules-git`, `rules-testing`, `rules-security`, `rules-api-rest`, `rules-database-postgres`, `rules-docker-ops`, `rules-backend-dotnet`, `rules-backend-node`, `rules-backend-python`, `rules-backend-rust`, `rules-frontend-react`, `rules-ui`, `rules-i18n`, `rules-skills`, plus deux packs `rules-pack-multitenant-postgres` et `rules-pack-audit-trail`. Raison : le champ `skills:` d'un agent précharge le contenu entier du skill au démarrage (doc Claude Code, sous-agents), donc aucune lecture de fichier hors du projet, et donc aucune demande d'accord.

2. **Format d'une règle.** Une puce par règle, qui commence exactement par `- **AT-<FAMILLE>-<NN>**` suivi du texte. Préfixe `AT-` pour ne jamais se confondre avec les identifiants d'un projet. Les identifiants sont ceux de l'inventaire.

3. **Qui charge quoi.** Chaque agent liste ses skills de règles dans son champ `skills:` :

| Agent | Skills de règles préchargés |
|---|---|
| front-react | index, git, testing, security, api-rest, frontend-react, ui, i18n, skills |
| back-csharp | index, git, testing, security, api-rest, database-postgres, docker-ops, backend-dotnet, i18n, skills |
| back-node | index, git, testing, security, api-rest, database-postgres, docker-ops, backend-node, i18n, skills |
| back-python | index, git, testing, security, api-rest, database-postgres, docker-ops, backend-python, i18n, skills |
| back-rust | index, git, testing, security, api-rest, database-postgres, docker-ops, backend-rust, i18n, skills |
| test-writer | index, git, testing, i18n |
| reviewer | index, git, testing, security, api-rest, database-postgres, docker-ops, frontend-react, ui, i18n, skills |
| security | index, security, api-rest, database-postgres, docker-ops |
| qa | index, ui, i18n, testing |
| doc-writer | index, git |
| challenger, product-owner | aucun |

   Les packs ne sont jamais préchargés : `rules-index` dit de les charger avec l'outil Skill quand le `CLAUDE.md` du projet contient la ligne `Packs ai-team : <noms>`. Un agent `general-purpose` lancé par `/cycle` pour une stack sans agent reçoit dans son dispatch la consigne de charger `rules-index`, `rules-git`, `rules-testing` et `rules-security` avec l'outil Skill.

4. **Priorité.** `rules-index` fixe l'ordre : `CLAUDE.md` global, `rules/team.md`, spec du projet, règles du projet (`rules/` ou `CLAUDE.md`), règles ai-team, skills. Un conflit est signalé, jamais tranché en silence : un agent en lecture seule le signale comme constat ; la session principale le note dans `docs/decisions.md` du projet s'il existe, sinon dans `.superpowers/progress.md`.

5. **Reviewer.** Format inchangé : première ligne `VERDICT: APPROVE` ou `VERDICT: REQUEST_CHANGES`, puis `[bloquant|mineur] fichier:ligne - problème - correction attendue`. Quand une règle s'applique, son identifiant suit `fichier:ligne` (`AT-GIT-05` ou l'identifiant du projet) ; un constat sans règle (bug, cas limite) n'en a pas. À la revue de branche de `/cycle`, GPT garde les mêmes consignes sans le texte des règles : il juge en indépendant ; seuls les constats Claude citent des règles.

6. **Mises à jour liées.**
   - `agents/front-react.md` : la ligne qui charge `frontend-design:frontend-design` pour toute apparence est restreinte aux pages vitrine (AT-SK-02).
   - `rules/team.md` : retirer `frontend-design` de la ligne front-react ; `superpowers:using-git-worktrees` seulement pour des tâches parallèles (AT-GIT-01) ; nouvelle section courte « Règles de dev » qui renvoie aux skills `rules-*`.
   - `skills/cycle/SKILL.md` : la règle de repli `general-purpose` renvoie aux skills `rules-*` ; le reste des règles git déjà écrites dans `/cycle` reste inchangé.
   - `README.md` (section Contenu) : liste des skills `rules-*`.

7. **Tests** (`tests/test_rules.py`, et `tests/test_agents.py` adapté) :
   - chaque skill `rules-*` existe, a un frontmatter `name` et `description`, et 110 lignes au plus ; total des skills hors packs 950 lignes au plus ;
   - chaque identifiant de l'inventaire est défini une fois et une seule (ligne `- **AT-...**`), et aucun identifiant défini n'est absent de l'inventaire ;
   - chaque agent déclare exactement les skills de règles du tableau de l'objectif 3 (le tableau est encodé dans le test) ;
   - `test_agents_skills_exist` accepte les skills du plugin (`skills/*/`) sous le nom retenu par la vérification de nommage (contraintes) ;
   - mots propres à un projet interdits hors des packs, insensible à la casse et en mots entiers : `Orbital`, `OrbitalInvest`, `BowTrail`, `Velzon`, `tenant`, `locataire` ;
   - la recherche de tiret cadratin, point médian et emoji passe de `rules/*.md` à `rules/**` et `skills/**` (`rglob`).

## Non-objectifs

DeepSeek et tableau de suivi : déjà couverts par `rules/team.md` et le skill `dashboard`. Agent `design`, `design-system`, templates : cycle 2. Skills `new-project`, `wrap`, hooks git, `settings.json` : cycle 3. Règles métier (multi-tenant hors pack, permissions Orbital, schéma d'audit, palette, domaine bowtrail). Synchronisation automatique avec les `rules/` des projets : les projets gardent les leurs, qui priment.

## Contraintes

- Aucune installation ; une règle qui suppose un outil ne s'applique que s'il est présent (AT-IDX-04).
- Nommage dans `skills:` non documenté pour un skill de plugin (`rules-git` ou `ai-team:rules-git`) : la première tâche du plan le vérifie en lançant un sous-agent de test et en lisant le journal de debug de Claude Code (un skill introuvable y est signalé), puis fixe le nom pour tout le reste.
- Le champ `skills:` précharge 32 skills au plus par agent ; le reviewer en a le plus (11 règles plus ses 3 skills actuels).
- Les règles du `CLAUDE.md` global priment (pas de push sans accord, pas de mention de Claude, compte GitHub selon le dossier).
- Tous les tests existants restent verts (75 à ce jour, `python3 -m unittest discover -s tests`).
- Vérification finale : depuis un dossier de test sans `rules/`, un sous-agent `reviewer` cite une règle `AT-` sans avoir lu de fichier hors du dossier. Si l'outil ne permet pas de le lancer depuis cette session, le test est décrit pas à pas pour Anthony.

## Arbitrages

Tranchés par Anthony : worktree seulement pour les tâches parallèles ; TDD partout ; fusion par la session principale seule ; `frontend-design` interdit sur les écrans d'application.

Choix de Claude : PR de 400 lignes strict (mesure dans AT-GIT-05) ; jamais `--force` ; `GH_TOKEN` partout, compte selon le `CLAUDE.md` global ; .NET option B par défaut, option A si le projet a déjà un Mediator ; gate de repli `make ci-local`, sinon `make test lint`, sinon la commande de test du plan ; règles en français ; noms de tests en anglais.

## Approches

1. Skills `rules-*` préchargés par les agents (choisie) : contenu dans le contexte de l'agent sans lecture de fichier, chargement ciblé par rôle.
2. Fichiers `rules/dev/` lus par les agents : rejetée, chaque lecture hors du projet demande un accord (règle globale « Accès aux données »).
3. Tout dans `rules/team.md` : rejetée, ce fichier est chargé dans toutes les sessions, environ 900 lignes de plus à chaque échange.
4. Un dépôt modèle copié dans chaque projet : rejetée, c'est la dérive qu'on veut éviter.

## Laissé au constructeur

La rédaction de chaque règle à partir de sa source et de sa ligne d'inventaire, les exemples de code par stack, l'ordre interne des skills.
