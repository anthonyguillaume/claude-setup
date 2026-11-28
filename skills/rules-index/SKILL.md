---
name: rules-index
description: "Règles de dev ai-team (index), préchargées par les agents. À charger avant d'écrire ou de relire du code, pour l'ordre d'autorité, les conflits et les packs."
---

# Règles index

Ordre d'autorité, gestion des conflits, packs et outils. Les autres skills de règles s'appellent `ai-team:rules-<thème>`.

- **AT-IDX-01** Ordre d'autorité, du plus fort au plus faible : `CLAUDE.md` global, `rules/team.md`, spec du projet, règles du projet (`rules/` ou `CLAUDE.md`), règles ai-team, skills.
- **AT-IDX-02** Un conflit entre deux sources est signalé, jamais tranché en silence. Un agent en lecture seule le signale comme constat ; la session principale le note dans `docs/decisions.md` du projet s'il existe, sinon dans `.superpowers/progress.md`.
- **AT-IDX-03** Les packs (`multitenant-postgres`, `audit-trail`) ne s'appliquent que si le `CLAUDE.md` du projet contient la ligne `Packs ai-team : <noms>`. L'agent charge alors le skill du pack avec l'outil Skill (`ai-team:rules-pack-multitenant-postgres`, `ai-team:rules-pack-audit-trail`).
- **AT-IDX-04** Une règle qui suppose un outil (gitleaks, Docker, Trivy, Semgrep, linter, cible `make`) ne s'applique que si l'outil est présent. Ne jamais installer un outil pour appliquer une règle.

## Qui charge quoi

Chaque agent précharge ces skills de règles (champ `skills:`), sans le préfixe `rules-`. Les packs ne sont jamais préchargés.

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

Un agent `general-purpose` lancé pour une stack sans agent dédié charge `rules-index`, `rules-git`, `rules-testing` et `rules-security` avec l'outil Skill.
