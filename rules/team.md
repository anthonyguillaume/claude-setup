# ai-team - règles communes

Chargé depuis `~/.claude/CLAUDE.md`. S'applique à toutes les sessions et à tous les agents.
Les règles du `CLAUDE.md` global (git, compte GitHub, périmètre, installations, accès aux données) priment toujours.

## 1. Modèles et rôles

- Orchestration, brainstorming, décisions : la session principale, idéalement sur Fable (`/model fable`).
- Second avis : GPT via `/debate`, `/verify` ou l'agent `challenger`. Jamais Claude qui se relit seul sur une décision importante.
- Travail mécanique à faible contexte : DeepSeek (section 4).
- Grok : uniquement quand l'utilisateur lance `/grok`.
- Images et vidéos : ComfyUI (`COMFYUI_URL`, défaut `http://192.168.0.96:8188`), chantier 3.
- Dans un projet qui a ses propres agents (`.claude/agents/`), ils priment sur ceux d'ai-team.

## 2. Quand demander un second avis

- `/debate` automatique dans `/cycle` : spec, plan, revue de fin de branche.
- Proposer `/debate` hors cycle pour : choix d'architecture, choix de librairie ou de service, analyse dont dépend une décision coûteuse, diagnostic de bug incertain.
- `/verify` est lancé par l'utilisateur ; le proposer quand une réponse repose sur une API, une option ou une version citée de mémoire.
- Désaccord Claude/GPT : on s'arrête, l'utilisateur tranche. Accord : on continue et on le trace dans `.superpowers/progress.md` sous la forme `Décision : ... - coût si faux : ...`.

## 3. Skills : qui les utilise et quand

| Phase / agent | Skills |
|---|---|
| Idée, produit (orchestrateur, product-owner) | `superpowers:brainstorming`, `epic-hypothesis`, `prioritization-advisor`, `roadmap-planning`, `workshop-facilitation` |
| Comprendre l'existant | `graphify`, `context-mode`, `context7` (docs de librairies à jour) |
| Spec, plan, architecture | `superpowers:writing-plans`, `archify` (diagrammes), `superpowers:using-git-worktrees` |
| Exécution du plan | `superpowers:subagent-driven-development`, `superpowers:dispatching-parallel-agents`, `delegate-to-deepseek`, `ponytail` (code minimal) |
| test-writer | `superpowers:test-driven-development` |
| front-react | `vercel-react-best-practices`, `impeccable`, `frontend-design`, `ui-ux-pro-max:ui-ux-pro-max`, `ui-ux-pro-max:ui-styling`, `ui-ux-pro-max:design-system`, `emil-design-eng` |
| front - pages publiques / vitrine | `design-taste-frontend` |
| front - animations | `emil-design-eng`, `review-animations` |
| back-csharp | `dotnet-webapi`, `optimizing-ef-core-queries`, `postgresql-optimization` |
| back-node | `postgresql-optimization`, `context7` |
| back-python | `context7` |
| back-rust | `context7` (aucun skill Rust installé → `find-skills` pour en chercher un) |
| Bug, test qui casse | `superpowers:systematic-debugging` |
| reviewer | `code-review`, `ponytail-review`, `simplify`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review` |
| Audit d'un repo entier | `ponytail-audit`, `ponytail-debt` |
| security | `owasp-security`, `differential-review`, `security-review`, `github-actions-hardening`, plugin `security-guidance` |
| qa | plugin Playwright, `run`, `superpowers:verification-before-completion` |
| doc-writer | `documentation-writer`, `archify` |
| Fin de branche | `superpowers:verification-before-completion`, `superpowers:finishing-a-development-branch` |
| Chantier 2 (GitHub, déploiement) | `github-actions-hardening`, `claude-approvals` ; `/ship` et `/steward` restent lancés par Anthony uniquement |
| Chantier 3 (contenu) | `ui-ux-pro-max:design`, `ui-ux-pro-max:banner-design`, `ui-ux-pro-max:brand`, `ui-ux-pro-max:slides`, `anthropic-skills:canvas-design`, connecteur Descript |
| Hors cycle, au cas par cas | `find-skills`, `dataviz`, `anthropic-skills:docx/xlsx/pptx/pdf`, plugins LSP `clangd-lsp` et `swift-lsp` (automatiques), skills Atlassian (travail Eurotunnel) |

Si aucun skill ne couvre un besoin récurrent : proposer `find-skills` à l'utilisateur (installation sur accord uniquement).

## 4. DeepSeek (MCP `deepseek`, skill `delegate-to-deepseek`)

- **Déléguer** seulement des unités complètes, mécaniques et **à faible contexte** : traductions, CRUD isolé, docs, scripts courts, correctifs de lint, résumés de suites de tests, scans en lecture seule. Leçon de bricktales : DeepSeek échoue dès qu'il doit lire beaucoup de code.
- **Jamais délégué** : authentification et session, autorisation et isolation des données, audit, cryptographie et secrets, architecture, arbitrages entre règles, revue finale. Doute : la tâche reste chez Claude.
- `flash` par défaut, `pro` seulement après un échec constaté de flash.
- Le `context` donne tout : chemins absolus, conventions, critères d'acceptation (commande et résultat attendu), interdits (pas de commit, pas de push, pas de lecture de `.env`, pas d'installation, pas de fichier hors périmètre).
- Claude vérifie toujours : relire le diff, relancer les tests, chercher les fichiers parasites, puis `get_deepseek_recovery` et `acknowledge_deepseek_mutations` avec les identifiants relus.

## 5. Confidentialité vers les autres modèles

- GPT reçoit uniquement la copie filtrée produite par `bin/snapshot.py` (fichiers suivis par git, sans secrets ni liens symboliques, `.aiignore` respecté), et Codex ne peut lire que cette copie.
- Jamais envoyé à GPT, DeepSeek ou Grok : `.env*`, clés, jetons (`GH_TOKEN`...), mots de passe, `~/.deepseek-mcp/`, données personnelles réelles, références artistiques privées.
- Grok ne reçoit que le texte du prompt, aucun fichier.
- Une clé ne s'affiche jamais, ne se colle jamais dans la conversation : elle vit dans `~/.zshrc`.

## 6. Commandes

- `/debate <question>`, `/verify`, `/grok <prompt>`, `/cycle <idée>`, `/dashboard [étape]` (tableau de suivi du projet, un artifact privé par projet). Si la forme courte ne répond pas, utiliser `/ai-team:<commande>`.
- Noms de commandes, skills et agents en anglais.

## 7. Écriture

- Pas de tiret cadratin, pas de point médian, pas d'emoji : utiliser `-`.
- Jamais de mention de Claude ni de `Co-Authored-By` dans les commits et les PR. Jamais de `git push` sans accord explicite.
