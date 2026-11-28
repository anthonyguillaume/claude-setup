---
name: rules-skills
description: "Règles de dev ai-team (skills), préchargées par les agents. À charger avant d'écrire ou de relire du code, pour choisir quel skill utiliser et quand."
---

# Règles skills

Quel skill à quel moment, et comment les maintenir.

- **AT-SK-01** Utiliser le skill du moment, parmi ceux installés par le manifeste du plugin : cadrage `superpowers:brainstorming` puis `superpowers:writing-plans` ; exécution `superpowers:subagent-driven-development`, `superpowers:using-git-worktrees` (tâches parallèles), `delegate-to-deepseek` ; code `superpowers:test-driven-development`, `ponytail:ponytail` ; API et données `dotnet-webapi`, `optimizing-ef-core-queries`, `postgresql-optimization` ; front `vercel-react-best-practices` (hors parties Next.js) ; bug `superpowers:systematic-debugging` ; avant PR `superpowers:verification-before-completion`, `simplify`, `ponytail:ponytail-review` ; revue `code-review`, `security-review`, `owasp-security`, `differential-review` ; CI `github-actions-hardening` ; fin de branche `superpowers:finishing-a-development-branch` ; UI `impeccable`, `ui-ux-pro-max:design-system`, `emil-design-eng` ; schémas `archify` ; documentation `documentation-writer` ; vérification visuelle `run` ; connaissance du code `graphify` ; grosses sorties `context-mode:context-mode`.
- **AT-SK-02** `frontend-design:frontend-design`, `design-taste-frontend` et `ui-ux-pro-max:brand` sont réservés aux pages vitrine. Pour les écrans d'application, utiliser `ui-ux-pro-max:ui-ux-pro-max` puis `impeccable`.
- **AT-SK-04** Les skills se mettent à jour un par un, après lecture du diff (contenu, scripts, téléchargements), jamais en masse ni globalement.
- **AT-SK-05** `differential-review` se lance seulement dans le worktree ou la branche de la PR relue, car il peut extraire des commits. Jamais dans le worktree d'une autre tâche ni dans le dépôt principal.
- **AT-SK-07** Un skill se charge seulement quand la tâche le demande, jamais "au cas où" : chaque chargement coûte du contexte.
