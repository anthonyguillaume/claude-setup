# Règles de développement génériques - design

Cycle 1 sur 3 du chantier « règles, design, nouveau projet ». Cycle 2 : agent `design` et templates de maquettes. Cycle 3 : skills `new-project` et `wrap`.

## Intention

Les projets d'Anthony (Orbital, OrbitalInvest, bowtrail) ont des règles de développement écrites dans `rules/`, qui se recopient et dérivent d'un projet à l'autre. Les agents d'ai-team n'en ont qu'une ligne ou deux chacun. But : une seule source de règles génériques dans le plugin, que chaque agent lit selon sa stack, et que les projets n'ont plus à recopier.

Succès : un agent ai-team lancé dans un projet sans `rules/` applique les mêmes règles que dans Orbital, moins le métier.

## Sources

- `/Users/anthonyguillaume/Dev/Orbital/rules/*.md` et `rules/agents/*.md` (source principale, identifiants de règles).
- `/Users/anthonyguillaume/Dev/OrbitalInvest/rules/` (trois motifs en plus : jeton machine comparé en temps constant, refus de démarrer sur un secret d'exemple, `FOR UPDATE` à la place d'un verrou consultatif ; DB-07 sans `tenant_id`).
- `/Users/anthonyguillaume/Dev/bowtrail/rules/` (version courte, plus stricte sur certains points).

Lecture seule de ces projets : rien n'y est modifié.

## Objectifs

1. Créer `rules/dev/` dans claude-setup, en français, avec les fichiers ci-dessous. Chaque règle garde l'identifiant de sa source (GIT-01, TST-08...) quand elle en a un ; les règles venues de bowtrail ou nouvelles prennent le numéro libre suivant de leur famille.

| Fichier | Règles source gardées | Lu par |
|---|---|---|
| `README.md` | index, ordre d'autorité « spec > règles du projet > rules/dev > skills », conflit noté dans `docs/decisions.md` (SK-06) | tous |
| `git-workflow.md` | GIT-01 (worktree seulement pour les tâches parallèles), 03, 05 (400 lignes strict), 06 (commande de gate du projet), 07, 08, 09, 10 (jamais `--force` sur aucune branche), 13 ; GIT-02 conditionnel ; GIT-11 en motif `GH_TOKEN`, jamais `gh auth switch` ; nommage `type/<scope>-<sujet>` et `--delete-branch` (bowtrail) | tous |
| `testing.md` | TST-01, 02 (TDD partout), 04 (cœur), 07 (principe), 08, 09, 10, 12 ; HTTP externe simulé, sortie de test propre (bowtrail) ; tableau d'outils par stack (.NET, Node, Python, Rust) | test-writer, reviewer, back-*, front-react |
| `security.md` | SEC-01, 02 (valeurs par défaut), 04 à 12, checklist, 13 (liste de chemins sensibles en modèle), table OWASP ; agents ne lisent jamais `.env`, validation des fichiers envoyés (bowtrail) ; AUTHZ-04 ; motifs OrbitalInvest | security, reviewer, back-*, front-react |
| `api-rest.md` | API-01 à 12 et 14 | back-*, front-react, reviewer |
| `database-postgres.md` | DB-01 à 12 (rôles `<app>_app` / `<app>_migrator`, DB-07 version OrbitalInvest) | back-*, reviewer |
| `docker-ops.md` | OPS-01 à 03, 05 à 08, 11, 12 ; GIT-12 et OPS-09 fusionnés en « CI sobre » | back-*, reviewer |
| `backend-dotnet.md` | BE-02, 03, 05, 06, 07, 10 à 16 ; option A Clean Architecture + Mediator (BE-01, 04, 08, 09), option B handlers par fonctionnalité sans Mediator (bowtrail) ; SOLID | back-csharp |
| `backend-node.md` | cœur neutre : BE-02, 05, 06, 07 (zod), 10, 12, 13, 14 ; FE-09, 12, 13 côté TS | back-node |
| `backend-python.md` | même cœur : typage, ruff et mypy s'ils sont installés, pas d'`except` muet, horloge injectée, validation aux frontières | back-python |
| `backend-rust.md` | même cœur : `Result` et `thiserror`, pas d'`unwrap` hors tests, clippy `-D warnings`, licences, horloge injectée | back-rust |
| `frontend-react.md` | FE-01 à 13, 15 ; UI-15 ; variante Next.js (bowtrail : composants serveur par défaut, `error.tsx`/`not-found.tsx`, état dans l'URL, thème jamais lu par le serveur) | front-react, reviewer |
| `ui.md` | UI-01 à 09, cibles 44 px mobile / 24 px ordinateur, parties accessibilité de UI-13 et UI-14, `popover`/`<dialog>` natifs, pas d'emoji ni de police d'icônes, transitions coupées en mouvement réduit | front-react, qa, reviewer |
| `i18n.md` | I18N-01 (langues en variable) à 08 | front-react, back-*, test-writer |
| `skills.md` | SK-01 (lignes limitées aux skills du plugin), SK-02 (`frontend-design`, `design-taste-frontend`, `brand` réservés aux pages vitrine), SK-04 (principe), SK-05, 06, 07 | tous |
| `packs/multitenant-postgres.md` | MT-04, 05, 06, 08, 11, TST-06 | si le projet l'active |
| `packs/audit-trail.md` | AUD-02, 03, 04, 05, 07, 08 en motif | si le projet l'active |

2. Mettre à jour les agents ai-team : chaque agent qui code ou relit a une ligne « Avant de commencer, lis : » avec ses fichiers de la colonne « Lu par », et applique les règles du projet en priorité quand il en a. Le reviewer cite l'identifiant de la règle dans chaque constat (`[bloquant] fichier:ligne - RÈGLE-ID - problème - correction`).

3. Retirer `frontend-design` de la ligne front-react de `rules/team.md` (SK-02), et y ajouter une section courte qui renvoie à `rules/dev/README.md`.

4. Tests dans `tests/test_rules.py` :
   - chaque fichier cité par un agent existe ;
   - aucun identifiant de règle en double entre fichiers ;
   - aucun nom propre à un projet hors `packs/` (`Orbital`, `orbital_`, `BowTrail`, `tenant` hors packs) ;
   - pas de tiret cadratin, point médian ni emoji dans `rules/**` (le test existant ne couvre que `rules/*.md`).

## Non-objectifs

DeepSeek et tableau de suivi déjà couverts par `rules/team.md` et le skill `dashboard` : pas de pack. Agent `design`, `design-system.md`, templates (cycle 2). Skills `new-project`, `wrap`, hooks git, `settings.json` (cycle 3). Règles métier : multi-tenant hors pack, permissions Orbital, schéma d'audit, palette, domaine bowtrail.

## Contraintes

- Aucune installation. Une règle qui suppose un outil (gitleaks, Docker, Trivy, Semgrep, cibles `make`, linters) dit « si l'outil est présent » et ne le fait jamais installer.
- Budget : environ 900 lignes au total pour `rules/dev/` hors packs ; aucun fichier au-delà de 110 lignes.
- Chemin : les agents trouvent `rules/dev/` à côté de `rules/team.md`, dont `~/.claude/CLAUDE.md` contient l'import absolu (`@<dépôt>/rules/team.md`, écrit par `bootstrap.sh`).
- Les règles du `CLAUDE.md` global priment (pas de push sans accord, pas de mention de Claude, compte GitHub).
- Les tests existants (75) restent verts.

## Arbitrages

Tranchés par Anthony : worktree seulement pour les tâches parallèles ; TDD partout ; fusion par la session principale seule ; `frontend-design` interdit sur les écrans d'application.

Choix de Claude : PR de 400 lignes strict ; jamais `--force` ; `GH_TOKEN` partout ; .NET en options A et B ; règles en français ; noms de tests en anglais, comme le code.

## Approches

1. Fichiers par thème dans `rules/dev/`, lus à la demande par les agents (choisie) : contexte réduit, même découpage qu'Orbital.
2. Tout dans `rules/team.md` : rejetée, ce fichier est chargé dans toutes les sessions, 900 lignes de plus coûteraient à chaque échange.
3. Un dépôt modèle à copier dans chaque projet : rejetée, c'est la dérive qu'on veut éviter.

## Laissé au constructeur

La formulation exacte de chaque règle, l'ordre interne des fichiers, les exemples de code par stack.
