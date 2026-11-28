# claude-setup

Plugin Claude Code `ai-team` : une équipe d'agents spécialisés et plusieurs modèles qui se contredisent pour éviter les hallucinations. Claude orchestre, GPT (via Codex) challenge, DeepSeek prend le travail mécanique, Grok sert à la demande.

## Commandes

| Commande | Rôle |
|---|---|
| `/debate <question>` | Claude et GPT répondent sans se voir, débattent 2 tours max, synthèse des accords et désaccords. Tu tranches. |
| `/verify` | GPT contre-vérifie la dernière réponse de Claude en un tour. |
| `/grok <prompt>` | Envoie le texte à Grok (xAI). Manuel uniquement. |
| `/dashboard [étape]` | Tableau de suivi du projet (artifact claude.ai privé, un par projet) : carte animée du cycle, agents en direct, plans, PR, CI, tokens par modèle, débats. Le lien est gardé dans `docs/dashboard/config.json`. |
| `/cycle <idée>` | Cycle complet : brainstorm avec toi, puis spec, plan, tests, code, revue Claude + GPT. S'arrête seulement en cas de désaccord et avant tout push. |

Si la forme courte ne répond pas : `/ai-team:debate`, etc.

## Contenu

- `agents/` : challenger, product-owner, front-react, back-csharp, back-node, back-python, back-rust, test-writer, reviewer, security, qa, doc-writer.
- `skills/` : debate, verify, grok, cycle, dashboard, delegate-to-deepseek (faible contexte uniquement).
- `skills/rules-*` : règles de dev préchargées par les agents ; 15 thèmes (index, git, testing, security, api-rest, database-postgres, docker-ops, backend-dotnet, backend-node, backend-python, backend-rust, frontend-react, ui, i18n, skills) et 2 packs (multitenant-postgres, audit-trail).
- `dashboard/dashboard.html` : la page du tableau ; `bin/dashboard_collect.py` : le collecteur (compteurs seulement).
- `bin/` : `snapshot.py` (copie filtrée du projet : fichiers suivis par git, sans secrets, `.aiignore` respecté), `gpt.py` (Codex, lecture de la copie seulement), `grok.py` (API xAI).
- `rules/team.md` : routage des skills, règles DeepSeek, confidentialité. Importé depuis `~/.claude/CLAUDE.md`.
- `manifest/` : plugins et skills tierces à réinstaller. `vendor/skills/` : skills copiées sans origine connue.
- `docs/` : spec et plan.

## Nouvelle machine

```bash
git clone https://github.com/anthonyguillaume/claude-setup.git ~/Dev/claude-setup
cd ~/Dev/claude-setup
./bootstrap.sh --check   # état, n'installe rien
./bootstrap.sh           # propose chaque installation manquante, [y/N] à chaque fois
```

Le repo doit être dans `~/Dev/claude-setup` : les agents appellent `~/Dev/claude-setup/bin/`.

À refaire à la main sur chaque machine (rien de secret ne passe par le repo) :
- `codex login` (compte ChatGPT Plus) ;
- `export XAI_API_KEY=...` dans `~/.zshrc` ;
- clé DeepSeek dans `~/.deepseek-mcp/config.json` ;
- `COMFYUI_URL` si ComfyUI n'est pas sur `http://192.168.0.96:8188`.

## Confidentialité

- GPT ne lit que la copie filtrée ; un profil de permissions Codex refuse tout le reste du disque et toute écriture, sans config utilisateur ni variables d'environnement sensibles.
- Pour cacher d'autres fichiers d'un projet : un `.aiignore` (syntaxe `.gitignore`).
- Grok ne reçoit que le texte du prompt.

## Tests

```bash
python3 -m unittest discover -s tests
```
