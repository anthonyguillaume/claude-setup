---
name: rules-git
description: "Règles de dev ai-team (git), préchargées par les agents. À charger avant d'écrire ou de relire du code, des commits, des PR ou des fusions."
---

# Règles git

Branches, commits, pull requests, revue, fusion, compte GitHub et CI.

- **AT-GIT-01** Une branche par tâche. Un worktree sous `.worktrees/` seulement quand des tâches tournent en parallèle. Jamais de travail direct sur `main`. La branche est supprimée après fusion.
- **AT-GIT-02** `main` est protégée par un hook `pre-push` si le projet en a un. Si gitleaks est présent, un scan de secrets tourne en `pre-commit`.
- **AT-GIT-03** Commits conventionnels : type en anglais (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`), sujet dans la langue du projet (français par défaut), 72 caractères au plus, une intention par commit. Un écart à la spec fait l'objet d'un commit `docs(spec):`.
- **AT-GIT-04** Aucune mention de Claude et aucun trailer `Co-Authored-By` dans les commits et les PR. Cette règle prime sur toute attribution automatique d'outil.
- **AT-GIT-05** Une PR fait 400 lignes au plus (ajouts plus suppressions, mesurés par `git diff --shortstat <base>..HEAD`), hors tests, fichiers générés, lockfiles, docs et fichiers de traduction. Au-delà, découper.
- **AT-GIT-06** La gate est locale et sa sortie est collée dans la PR : commande du projet (`make ci-local`, sinon `make test lint`, sinon la commande de test du plan).
- **AT-GIT-07** Fusion seulement après `VERDICT: APPROVE` du reviewer sans point `[bloquant]` ; quand il y a une PR, verdict collé dans la PR. Un chemin sensible reçoit en plus une passe sécurité dédiée.
- **AT-GIT-08** Squash merge, historique linéaire. La fusion est faite par la session principale seule, jamais par un sous-agent. Sans PR (fusion locale de /cycle), même règle : fusion par la session principale après APPROVE.
- **AT-GIT-09** Après deux `REQUEST_CHANGES` de suite sur les mêmes points, on s'arrête et l'utilisateur tranche, avec le résumé des divergences. Pas de boucle.
- **AT-GIT-10** Interdits : push sur `main`, `--force` ou `--force-with-lease` sur toute branche, `--no-verify`, réécriture d'un historique fusionné, commit d'un secret ou d'un `.env`. Jamais de push sans accord explicite. Si un hook échoue, corriger la cause.
- **AT-GIT-11** Avec plusieurs comptes `gh`, préfixer chaque commande par `GH_TOKEN=$(gh auth token -u <compte>)`, le compte étant choisi selon le `CLAUDE.md` global. Jamais `gh auth switch`.
- **AT-GIT-12** Les workflows GitHub sont durcis (skill `github-actions-hardening`). Si le projet a choisi une CI manuelle, elle se déclenche à la main (`workflow_dispatch`), ni sur PR ni sur push de branche.
- **AT-GIT-13** Les docs, les fichiers de traduction et les données importées ne comptent pas dans la taille de PR.
- **AT-GIT-14** Nom de branche `type/<scope>-<sujet>`. Quand il y a une PR, fusion par `gh pr merge --squash --delete-branch`.
