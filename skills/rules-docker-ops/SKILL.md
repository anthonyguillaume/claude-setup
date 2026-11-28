---
name: rules-docker-ops
description: "Règles de dev ai-team (Docker et exploitation), préchargées par les agents. À charger avant d'écrire ou de relire du code de Dockerfile, de compose, de santé, de journaux ou de CI."
---

# Règles Docker et exploitation

Portée : fichiers compose, Dockerfiles, santé, journaux, télémétrie, CI. Chaque outil cité s'utilise si l'outil est présent, sans jamais l'installer.

- **AT-OPS-01** `docker compose up` lance toute l'application (base avec healthcheck, service de migration qui s'exécute puis s'arrête, API, front). Les dépendances utilisent `depends_on` avec `condition: service_healthy` ou `service_completed_successfully` (l'API attend la migration, qui attend la base). Un fichier de surcharge de développement, chargé automatiquement, ajoute le hot reload et les ports locaux.
- **AT-OPS-02** Toute variable requise s'écrit `${VAR:?message explicite}` : le démarrage échoue clairement si elle manque. Aucun défaut pour un secret. `.env.example` liste toutes les variables sans valeur réelle ; `.env` est ignoré par git. Les chaînes de connexion `<app>_app` et `<app>_migrator` sont distinctes.
- **AT-OPS-03** Les migrations s'exécutent dans un service dédié (cible de migration du Dockerfile, rôle `<app>_migrator`), jamais au démarrage de l'API, qui ne connaît que `<app>_app`.
- **AT-OPS-05** Dockerfiles multi-étapes (build séparé de l'exécution), image de base épinglée par digest (`image@sha256:...`, tag en commentaire), utilisateur non root, aucun secret, `.dockerignore`, `HEALTHCHECK` (ou porté par le compose).
- **AT-OPS-06** Les tests et le lint tournent en conteneurs : seuls Docker et Git sont requis sur la machine. Cibles `make` usuelles si l'outil est présent : `up`, `down`, `test`, `lint`, `migrate`, `e2e`, `ci-local`.
- **AT-OPS-07** L'API expose `/health/live` (le processus répond, sans dépendance) et `/health/ready` (base joignable, migrations appliquées). Les healthchecks compose utilisent `ready`. Un service non prêt ne reçoit pas de trafic.
- **AT-OPS-08** Journaux structurés (JSON) sur la sortie standard, jamais dans des fichiers du conteneur, sans donnée personnelle. Le `traceId` figure dans les logs et dans les erreurs de l'API. Si OpenTelemetry est présent, traces et métriques sont émises en OTLP, exporteur configuré par variables d'environnement.
- **AT-OPS-09** CI sobre : si le projet a choisi une CI manuelle, aucun workflow automatique sur pull request ni sur push de branche ; la publication sur tag `v*` reste permise. La gate locale (build, lint, tests, OpenAPI et client sans diff, gitleaks et scans si les outils sont présents) fait foi, son résultat est collé dans la PR. Le workflow GitHub se lance à la main (`workflow_dispatch`) avant une mise en production ou après une montée majeure de dépendance, et sur tag `v*` pour publier l'image, avec un scan avant publication si l'outil est présent.
- **AT-OPS-11** Le compose de production fixe `restart: unless-stopped` et des limites de ressources (CPU, mémoire) pour chaque service.
- **AT-OPS-12** Runtimes et frameworks restent sur une version LTS (par exemple .NET 10, Node 24 à la rédaction de la règle, PostgreSQL en version majeure supportée), ainsi que leurs images de base. Jamais de version non LTS (Node impair, .NET STS). Le passage à la LTS suivante est une migration décidée, jamais une PR automatique ; les montées majeures de ces runtimes sont ignorées par le robot de dépendances.
