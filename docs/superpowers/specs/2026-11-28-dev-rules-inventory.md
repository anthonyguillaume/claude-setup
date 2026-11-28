# Inventaire des règles génériques

Annexe de `2026-11-28-dev-rules-design.md`. Une ligne par règle : identifiant final, source, comportement attendu. Les identifiants finaux portent le préfixe `AT-` (ai-team) pour ne jamais se confondre avec les identifiants d'un projet. Le numéro reprend celui de la source quand il existe ; une règle nouvelle ou venue de bowtrail prend le numéro qui suit le plus grand numéro source de sa famille.

Sources : O = Orbital, OI = OrbitalInvest, B = bowtrail.

## rules-index
- AT-IDX-01 (nouvelle) : ordre d'autorité : `CLAUDE.md` global, `rules/team.md`, spec du projet, règles du projet, règles ai-team, skills.
- AT-IDX-02 (O SK-06, B README) : un conflit entre deux sources est signalé, jamais tranché en silence ; la session principale le note dans `docs/decisions.md` du projet s'il existe, sinon dans `.superpowers/progress.md`.
- AT-IDX-03 (nouvelle) : les packs (`multitenant-postgres`, `audit-trail`) ne s'appliquent que si le `CLAUDE.md` du projet contient la ligne `Packs ai-team : <noms>` ; l'agent charge alors le skill du pack avec l'outil Skill.
- AT-IDX-04 (nouvelle) : une règle qui suppose un outil (gitleaks, Docker, Trivy, Semgrep, linter, cible `make`) ne s'applique que si l'outil est présent ; jamais d'installation.

## rules-git
- AT-GIT-01 (O GIT-01, B) : une branche par tâche ; worktree sous `.worktrees/` seulement quand des tâches tournent en parallèle ; jamais de travail direct sur `main` ; branche supprimée après fusion.
- AT-GIT-02 (O GIT-02) : `main` protégée par un hook `pre-push` si le projet en a un ; scan de secrets en `pre-commit` si gitleaks est présent.
- AT-GIT-03 (O GIT-03, B) : Conventional Commits, type en anglais, sujet dans la langue du projet (français par défaut), 72 caractères au plus, une intention par commit ; écart à la spec dans un commit `docs(spec):`.
- AT-GIT-04 (O GIT-04, B) : aucune mention de Claude, aucun `Co-Authored-By`, dans les commits et les PR.
- AT-GIT-05 (O GIT-05, B) : PR de 400 lignes au plus, mesurées par `git diff --shortstat <base>..HEAD` (ajouts plus suppressions) hors tests, fichiers générés, lockfiles, docs et fichiers de traduction ; au-delà, découper.
- AT-GIT-06 (O GIT-06) : la gate est locale et sa sortie va dans la PR ; commande du projet (`make ci-local`, sinon `make test lint`, sinon la commande de test du plan).
- AT-GIT-07 (O GIT-07) : fusion seulement après `APPROVE` du reviewer sans `[bloquant]` ; passe sécurité dédiée sur les chemins sensibles.
- AT-GIT-08 (O GIT-08) : squash merge, historique linéaire, fusion par la session principale seule (jamais par un sous-agent).
- AT-GIT-09 (O GIT-09) : deux `REQUEST_CHANGES` de suite sur les mêmes points : on s'arrête, l'utilisateur tranche.
- AT-GIT-10 (O GIT-10, B) : jamais de push sur `main`, jamais `--force` ni `--force-with-lease` sur aucune branche, jamais `--no-verify`, jamais réécrire un historique fusionné, jamais de secret ni de `.env` commité ; jamais de push sans accord explicite.
- AT-GIT-11 (O GIT-11) : plusieurs comptes `gh` : `GH_TOKEN=$(gh auth token -u <compte>)` par commande, compte choisi selon le `CLAUDE.md` global ; jamais `gh auth switch`.
- AT-GIT-12 (O GIT-12) : workflows GitHub durcis (skill `github-actions-hardening`) ; CI déclenchée à la main si le projet l'a choisi.
- AT-GIT-13 (O GIT-13) : docs, fichiers de traduction et données importées ne comptent pas dans la taille de PR.
- AT-GIT-14 (B) : nom de branche `type/<scope>-<sujet>` ; `gh pr merge --squash --delete-branch`.

## rules-testing
- AT-TST-01 (O TST-01) : un test protège un comportement ou une règle (« échoue si on casse ... ») ; sinon il n'est pas écrit.
- AT-TST-02 (O TST-02, B) : TDD partout : test rouge pour la bonne raison, puis code, puis vert ; un bug corrigé a un test qui échouait avant.
- AT-TST-04 (O TST-04) : par endpoint : cas nominal, 422, 401, 403, 404 ; plus isolation et audit si les packs sont actifs.
- AT-TST-07 (O TST-07) : seuil de couverture seulement sur la couche domaine ; ailleurs mesuré sans seuil.
- AT-TST-08 (O TST-08) : tests interdits : getters et DTO, le framework lui-même, mock qui se teste lui-même, même cas à deux niveaux, snapshots complets.
- AT-TST-09 (O TST-09) : déterministe : pas de sleep, pas d'horloge réelle, pas d'ordre entre tests, pas de donnée mutable partagée.
- AT-TST-10 (O TST-10) : Arrange / Act / Assert lisible, builders dans le projet de test, `getByRole` avant `getByTestId`.
- AT-TST-12 (O TST-12) : test instable corrigé ou supprimé sous 48 h ; un test ignoré pointe vers une dette notée.
- AT-TST-13 (B) : HTTP externe toujours simulé, jamais de réseau réel ; pas de base en mémoire à la place de la vraie base.
- AT-TST-14 (B) : sortie de test propre, sans avertissement.
- AT-TST-15 (nouvelle) : outils par stack : .NET xUnit + Shouldly (+ Testcontainers si Docker), Node Vitest + Testing Library, Python pytest sinon unittest, Rust `cargo test` ; E2E Playwright + axe si présents ; noms de tests en anglais.

## rules-security
- AT-SEC-01 (O SEC-01) : cookie de session `HttpOnly`, `Secure`, `SameSite=Lax`, préfixe `__Host-` ; antiforgery sur toutes les écritures ; 415 sur les autres types de contenu.
- AT-SEC-02 (O SEC-02) : mots de passe : hachage lent (PBKDF2 ou mieux), 12 caractères minimum, liste de mots de passe courants, verrouillage 5 essais / 15 min, lien de réinitialisation à usage unique d'une heure.
- AT-SEC-03 (O SEC-03, OI) : garde « dernier administrateur actif » sous verrou (consultatif ou `SELECT ... FOR UPDATE`).
- AT-SEC-04 (O SEC-04) : rien de sensible dans le stockage navigateur, aucun secret dans le bundle front.
- AT-SEC-05 (O SEC-05) : pas d'injection : SQL paramétré, pas de HTML brut non assaini, pas de shell construit depuis une entrée, liste blanche contre le SSRF.
- AT-SEC-06 (O SEC-06) : limitation de débit stricte sur l'authentification et globale ; 429 avec `Retry-After`.
- AT-SEC-07 (O SEC-07) : anti-énumération : mêmes réponses et mêmes temps pour un compte existant ou non.
- AT-SEC-08 (O SEC-08, AUTHZ-04) : refus par défaut, marqueur d'accès explicite sur chaque endpoint, contrôle de l'objet (BOLA), DTO seulement ; droits relus à chaque requête, jamais stockés dans le cookie.
- AT-SEC-09 (O SEC-09) : CSP stricte, HSTS, nosniff, Referrer-Policy, Permissions-Policy, `frame-ancestors` ; CORS fermé par défaut.
- AT-SEC-10 (O SEC-10, B) : secrets hors du code (variables d'environnement, `.env.example` sans valeur) ; les agents ne lisent jamais `.env` ; rotation en cas de fuite.
- AT-SEC-11 (O SEC-11) : chaîne d'approvisionnement : versions épinglées, lockfiles, licences permissives, scans si les outils sont présents.
- AT-SEC-12 (O SEC-12) : aucune donnée personnelle dans les logs, identifiants techniques seulement.
- AT-SEC-13 (O SEC-13) : chemins sensibles (auth, autorisation, isolation, crypto, secrets, upload, CI) : passe de l'agent `security` avec `owasp-security` et `differential-review`, jamais délégué à DeepSeek.
- AT-SEC-14 (B) : fichiers envoyés : type vérifié par signature, taille maximale, `nosniff`.
- AT-SEC-15 (OI) : jeton machine comparé en temps constant ; l'application refuse de démarrer si un secret a encore sa valeur d'exemple.
- Checklist de PR (O) : 8 points, sans ceux des packs ; table OWASP ASVS 5.0 L2 et API Top 10 (O).

## rules-api-rest
- AT-API-01 (O API-01) : `/api/v1`, ressources au pluriel en kebab-case, JSON en camelCase, pas de verbe dans l'URL.
- AT-API-02 (O API-02) : identifiants UUID opaques, contrôle de l'objet à chaque accès.
- AT-API-03 (O API-03) : table verbes et codes (201 + `Location`, 204, 409, 412, 422, 429) ; jamais 200 avec une erreur dans le corps.
- AT-API-04 (O API-04) : PUT et DELETE idempotents.
- AT-API-05 (O API-05) : erreurs RFC 9457 `application/problem+json` avec `code` et `traceId`.
- AT-API-06 (O API-06) : aucune fuite dans un 500 ; pas de distinction 404 / 403 quand elle révèle quelque chose.
- AT-API-07 (O API-07) : 422 avec `errors: [{field, code}]`.
- AT-API-08 (O API-08) : pagination par curseur, `limit` 20 par défaut et 100 au plus, pas d'offset, index justifié.
- AT-API-09 (O API-09) : filtres nommés, tri `sort=champ:sens` sur liste blanche, paramètre inconnu : 400.
- AT-API-10 (O API-10) : ETag sur les ressources modifiables, `If-Match` périmé : 412.
- AT-API-11 (O API-11) : `traceId` sur chaque réponse, UTF-8, dates ISO en UTC.
- AT-API-12 (O API-12) : OpenAPI générée et comparée, client régénéré ; rupture de contrat : `/v2`.
- AT-API-14 (O API-14) : `If-Match` absent sur une écriture qui l'exige : 428.

## rules-database-postgres
- AT-DB-01 (O DB-01) : snake_case partout, préfixes `pk_`, `fk_`, `uq_`, `ck_`, `ix_`, aucun identifiant entre guillemets.
- AT-DB-02 (O DB-02) : `timestamptz` en UTC, `date` pour une date seule.
- AT-DB-03 (O DB-03) : clés UUID v7 générées par l'application.
- AT-DB-04 (O DB-04) : invariants en contraintes de base, énumérations en texte + check, concurrence par version.
- AT-DB-05 (O DB-05) : deux rôles `<app>_migrator` et `<app>_app`, moindre privilège, `GRANT` explicites.
- AT-DB-06 (O DB-06) : une migration réversible au plus par PR, jouée à part, jamais modifiée après fusion.
- AT-DB-07 (OI DB-07) : toute requête de liste a un index, colonnes de filtre et de tri en tête ; `EXPLAIN (ANALYZE, BUFFERS)` collé dans la PR.
- AT-DB-08 (O DB-08) : lectures par projection et sans suivi (`AsNoTracking` en EF), pas d'Include en cascade.
- AT-DB-09 (O DB-09) : pas de N+1, SQL brut paramétré.
- AT-DB-10 (O DB-10) : une transaction par requête, verrous consultatifs transactionnels seulement.
- AT-DB-11 (O DB-11) : colonnes de données personnelles listées dans un registre, aucun secret en clair.
- AT-DB-12 (O DB-12) : 30 requêtes SQL au plus par requête HTTP, vérifié en test si la stack le permet.

## rules-docker-ops
- AT-OPS-01 (O OPS-01) : `docker compose up` lance tout ; dépendances sur healthcheck ; surcharge de dev.
- AT-OPS-02 (O OPS-02) : `${VAR:?message}` pour les variables obligatoires, aucun défaut pour un secret, `.env.example`.
- AT-OPS-03 (O OPS-03) : migrations dans un service dédié, jamais au démarrage de l'API.
- AT-OPS-05 (O OPS-05) : images multi-étapes, base épinglée par digest, utilisateur non root, `.dockerignore`, HEALTHCHECK.
- AT-OPS-06 (O OPS-06) : tests et lint en conteneur, seuls Docker et Git requis sur la machine.
- AT-OPS-07 (O OPS-07) : `/health/live` et `/health/ready`.
- AT-OPS-08 (O OPS-08) : logs JSON sur stdout, `traceId` dans les logs, OpenTelemetry si présent.
- AT-OPS-09 (O OPS-09 + GIT-12) : CI sobre : gate locale qui fait foi, CI manuelle, image publiée sur tag avec scan si l'outil est présent.
- AT-OPS-11 (O OPS-11) : compose de prod avec `restart: unless-stopped` et limites de ressources.
- AT-OPS-12 (O OPS-12) : runtimes LTS seulement.

## rules-backend-dotnet
- AT-BE-02 (O BE-02) : organisation par fonctionnalité, un dossier par cas d'usage, pas d'import entre fonctionnalités.
- AT-BE-03 (O BE-03) : handlers `internal sealed`.
- AT-BE-05 (O BE-05) : `Result<T>` avec un `Error.Code` stable en anglais ; exceptions pour l'imprévu seulement.
- AT-BE-06 (O BE-06) : codes d'erreur = contrat : jamais renommés ni réutilisés, traductions dans la même PR.
- AT-BE-07 (O BE-07) : validation dans le pipeline, erreurs par champ, invariants dans les entités.
- AT-BE-10 (O BE-10) : interface seulement à une vraie frontière ou une vraie variation.
- AT-BE-11 (O BE-11) : `TimeProvider`, jamais `DateTime.Now`, UTC.
- AT-BE-12 (O BE-12) : async de bout en bout avec `CancellationToken`, pas de `.Result`, `.Wait()` ni `async void`.
- AT-BE-13 (O BE-13) : `[LoggerMessage]`, messages en anglais, aucune donnée personnelle.
- AT-BE-14 (O BE-14) : `TreatWarningsAsErrors`, Nullable, analyseurs, versions centralisées, lockfiles, versions vérifiées en ligne.
- AT-BE-15 (O BE-15) : conventions C# Microsoft, `dotnet format --verify-no-changes`.
- AT-BE-16 (O BE-16) : code en anglais, commentaires dans la langue du projet pour le pourquoi, pas de `TODO` sans dette notée.
- AT-BE-17 (O BE-01, 04, 08, 09) : option A : Clean Architecture (Api, Application, Domain, Infrastructure), Mediator, pipeline validation puis transaction puis handler, DbContext étroit.
- AT-BE-18 (B) : option B, par défaut quand le projet n'a pas de Mediator : endpoints par fonctionnalité avec handlers statiques, sans Mediator ni CQRS.
- Section SOLID (O).

## rules-backend-node
- AT-BN-01 (O BE-02) : organisation par fonctionnalité.
- AT-BN-02 (O BE-05, 06) : erreurs typées avec un code stable, jamais renommé.
- AT-BN-03 (O BE-07) : validation zod aux frontières.
- AT-BN-04 (O BE-10) : abstraction seulement à une vraie frontière.
- AT-BN-05 (O BE-12) : async avec `AbortSignal`, aucune promesse non attendue.
- AT-BN-06 (O BE-13) : logs structurés, aucune donnée personnelle.
- AT-BN-07 (O BE-14, FE-09, 12, 13) : TypeScript strict, pas de `any`, lockfile, licences permissives, versions vérifiées dans le registre, pas de librairie pour dix lignes.

## rules-backend-python
- AT-BP-01 (O BE-02) : organisation par fonctionnalité.
- AT-BP-02 (O BE-05, 06) : exceptions métier avec un code stable ; jamais d'`except` muet.
- AT-BP-03 (O BE-07) : validation aux frontières (pydantic si présent, sinon code explicite).
- AT-BP-04 (O BE-11) : horloge injectée, UTC.
- AT-BP-05 (O BE-13) : `logging` structuré, aucune donnée personnelle.
- AT-BP-06 (O BE-14) : typage, ruff et mypy s'ils sont installés, dépendances épinglées, licences permissives.

## rules-backend-rust
- AT-BR-01 (O BE-02) : organisation par module de fonctionnalité.
- AT-BR-02 (O BE-05, 06) : `Result` avec des erreurs `thiserror` à code stable ; pas d'`unwrap` hors tests.
- AT-BR-03 (O BE-11) : horloge injectée.
- AT-BR-04 (O BE-13) : `tracing`, aucune donnée personnelle.
- AT-BR-05 (O BE-14) : `cargo clippy -- -D warnings`, `cargo fmt --check`, licences vérifiées (`cargo deny` si présent).

## rules-frontend-react
- AT-FE-01 à AT-FE-13, AT-FE-15 (O FE-01 à 13, 15) : structure `app/`, `features/`, `shared/` ; imports `shared` vers `features` vers `app` ; pas de barrels géants ; TanStack Query pour les appels serveur ; client généré jamais modifié ; préférence d'état locale, dérivée, URL, contexte étroit ; validation client pour l'UX, serveur qui fait foi ; primitives accessibles enveloppées dans `shared/ui` ; TS strict ; `useEffect` rare, mémoïsation après mesure ; mobile d'abord, vérifié à 360 et 1280 px ; exports nommés ; pas de librairie pour dix lignes ; pas d'`enum` TS.
- AT-FE-16 (O UI-15) : formulaires : messages traduits, `aria-describedby`, `aria-invalid`, focus sur la première erreur.
- AT-FE-17 (B) : variante Next.js : composants serveur par défaut, `"use client"` seulement pour l'interaction, `error.tsx` et `not-found.tsx` par segment, filtres dans l'URL, thème jamais lu par le serveur.

## rules-ui
- AT-UI-01 à AT-UI-09 (O UI-01 à 09) : tokens seulement ; clair et sombre ; texte 12 px minimum, corps 14 px ; WCAG 2.2 AA, la couleur ne porte jamais seule l'information ; jamais d'impasse ; libellé humain d'abord ; états complets (chargement, vide, erreur, succès) et confirmation des actions destructives ; ouvrir la maquette avant de construire un écran quand le projet en a ; élément utilisé deux fois : primitive partagée.
- AT-UI-16 (O UI-12, B) : cibles tactiles de 44 px sur mobile, 24 px sur ordinateur.
- AT-UI-17 (O UI-13, 14, B) : icône décorative `aria-hidden`, bouton icône avec un libellé, graphique avec titre, légende et table de données ; pas d'emoji ni de police d'icônes.
- AT-UI-18 (B) : `popover` et `<dialog>` natifs ; transitions de 150 ms coupées en mouvement réduit.

## rules-i18n
- AT-I18N-01 à AT-I18N-08 (O I18N-01 à 08) : langues du projet en variable (français par défaut) ; aucune chaîne en dur ; une clé par sens, pas de concaténation ; pluriels ICU et `Intl` ; erreurs d'API traduites depuis `code` ; codes serveur en anglais ; test de parité des clés ; ajouter une langue = ajouter des fichiers.

## rules-skills
- AT-SK-01 (O SK-01) : quel skill à quel moment, limité aux skills installés par le manifeste du plugin.
- AT-SK-02 (O SK-02) : `frontend-design:frontend-design`, `design-taste-frontend` et `ui-ux-pro-max:brand` réservés aux pages vitrine ; écrans d'application : `ui-ux-pro-max:ui-ux-pro-max` puis `impeccable`.
- AT-SK-04 (O SK-04) : skills mis à jour un par un après lecture du diff, jamais en masse.
- AT-SK-05 (O SK-05) : `differential-review` seulement dans le worktree ou la branche de la PR.
- AT-SK-07 (O SK-07) : un skill se charge seulement quand la tâche le demande.

## rules-pack-multitenant-postgres
- AT-MT-04, 05, 06, 08, 11 (O MT-04, 05, 06, 08, 11) et AT-TST-06 (O TST-06) : filtre global par locataire ; RLS `ENABLE` + `FORCE` avec `WITH CHECK` ; `set_config(..., true)`, jamais `SET` de session ; ressource d'un autre locataire : 404 ; test du schéma RLS.

## rules-pack-audit-trail
- AT-AUD-02, 03, 04, 05, 07, 08 (O AUD) : secrets masqués ; entrée d'audit dans la même transaction que l'action ; liste minimale d'événements de sécurité ; audit opt-in par marqueur ; table en ajout seul (trigger et droits) ; chaînage par hash sous verrou.
