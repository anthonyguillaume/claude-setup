# Équipe multi-agents multi-modèles - conception (chantier 1 : cycle de dev)

Date : 2026-11-27 - Statut : brouillon à valider

## Intention

Anthony constate qu'un modèle affirme ou génère souvent quelque chose de faux et ne le reconnaît que quand on lui demande de vérifier. Il veut :

1. **Que la vérification soit faite par un autre modèle**, automatiquement, au lieu de compter sur l'auto-relecture.
2. **Deux avis indépendants sur les décisions et analyses**, qui débattent ; lui tranche.
3. **Utiliser chaque modèle pour ce qu'il fait le mieux** (Fable orchestre et brainstorme, GPT challenge Fable, ComfyUI pour image/vidéo, DeepSeek pour le mécanique).
4. **Réduire le coût en tokens Claude** en déléguant ce qui peut l'être.
5. **Un vrai cycle de travail** avec des agents spécialisés, réutilisable dans tous ses projets.

Modèles disponibles : Claude (abonnement), ChatGPT (abonnement, app « ChatGPT Classic »), DeepSeek (déjà branché en MCP : `~/Dev/mcp/deepseek-as-subagent`, modèles `flash`/`pro`), ComfyUI (machine LAN `http://192.168.0.96:8188`, client existant `crushed/tools/comfyui.py`).

## Ce qui existe déjà (à réutiliser, pas à réinventer)

- **Orbital / OrbitalInvest** : agents orchestrator/backend/frontend/reviewer (opus) + test-writer (sonnet) ; cycle brainstorm → plan → worktree → tests d'abord → code → `make ci-local` → reviewer `VERDICT: APPROVE` → squash merge ; 2 `REQUEST_CHANGES` → escalade humaine. Règles DeepSeek `rules/deepseek.md` (DS-02 : jamais délégué : auth, isolation des données, audit, crypto, architecture, revue finale ; DS-06/07 : vérification et acquittement des mutations).
- **bricktales** : `agents/models.yaml` (paliers de modèles, rôles, escalade, budgets - non appliqués) ; leçon : **DeepSeek échoue sur les tâches à gros contexte** (le budget de son MCP croît au carré de l'historique) → limité aux tâches à faible contexte.
- **crushed** : journal `progress.md` avec « Ruling : … - coût si faux : … », vérifications d'interfaces entre tâches avant de lancer, choix non validés marqués `[choix de Claude]`.
- **Superpowers** (plugin global) : brainstorming → writing-plans → subagent-driven-development, déjà utilisé partout.
- **Skills installées** utiles aux agents : `vercel-react-best-practices`, `impeccable`, `dotnet-webapi`, `optimizing-ef-core-queries`, `owasp-security`, `differential-review`, `code-review`, `ponytail-audit`, `delegate-to-deepseek`, Playwright (plugin).

## Contrainte technique structurante

Un sous-agent Claude Code ne tourne que sur un modèle Claude (fable/opus/sonnet/haiku). **GPT, DeepSeek et ComfyUI sont des outils** qu'un agent Claude appelle (CLI via Bash, MCP, script). Chaque « agent GPT » est donc un agent Claude léger qui relaie vers GPT, ou un appel direct de l'orchestrateur.

## Objectifs

- Équipe d'agents **globale** dans `~/.claude/agents/`, utilisable dans n'importe quel projet.
- Commande **`/debate`** : Claude et GPT répondent indépendamment, débattent au plus 2 tours, synthèse des accords/désaccords ; Anthony tranche.
- **Cycle de dev autonome** qui ne s'arrête pour Anthony **que quand Claude et GPT sont en désaccord** (et avant tout `git push`, voir contraintes).
- Routage du travail mécanique vers DeepSeek, avec les règles d'Orbital passées au niveau global.

## Non-objectifs (chantiers suivants)

- Chantier 2 : GitHub (PR, issues, workflows Actions) et déploiement - hébergement encore inconnu.
- Chantier 3 : contenu - agents image/vidéo ComfyUI, site vitrine, community manager Instagram/TikTok.
- Faire respecter des budgets en dollars ou une escalade automatique par du code (l'option « orchestrateur externe » est écartée pour l'instant).
- Gemini, Ollama, modèles locaux.

## Anti-objectifs (échec même si ça « marche »)

- **Débat de façade** : GPT qui approuve tout par politesse, ou les deux modèles qui voient la réponse de l'autre avant d'avoir produit la leur.
- **Arrêts trop fréquents** : si le cycle s'arrête à chaque étape, l'outil ne sert à rien.
- **GPT ou DeepSeek qui modifient des fichiers sans contrôle**, ou à qui on envoie des secrets.
- **Coût en hausse** : le débat systématique ne doit pas annuler l'économie de DeepSeek.

## Contraintes

- `git push` jamais sans accord explicite (CLAUDE.md global) → **arrêt systématique avant push**, même en cas d'accord.
- Pas de mention de Claude dans les commits/PR (CLAUDE.md global).
- Toute installation (Codex CLI) demande l'accord d'Anthony au moment de la faire.
- Modifications hors du dossier de lancement : accord requis. La mise en place se fait dans `~/.claude` ; toucher aux projets (Orbital, etc.) est hors périmètre de ce chantier.
- Confidentialité : ne jamais envoyer à GPT ni DeepSeek `.env`, tokens (`GH_TOKEN`…), clés, `~/.deepseek-mcp/`, références artistiques privées (règle reprise de bricktales).
- Les agents de projet (ex. `Orbital/.claude/agents/backend.md`) restent prioritaires sur les agents globaux de même nom : ne pas casser les projets existants.

## Approches envisagées

| | Description | Compromis |
|---|---|---|
| **A - Base globale + GPT via Codex CLI (retenue)** | Agents dans `~/.claude/agents`, skill `/debate`, GPT appelé via `codex exec` en lecture seule, `codex exec resume` pour enchaîner les tours | Le moins de pièces, réutilise l'existant ; les règles de coût sont des consignes, pas des plafonds |
| B - Idem, GPT via `codex mcp-server` | GPT devient un outil MCP natif | Un serveur de plus pour un gain faible |
| C - Orchestrateur externe (Python + `models.yaml` appliqué) | Budgets et escalade réellement contrôlés | Vrai logiciel à maintenir, sort de Claude Code |

Choix : **A**, proposé par Claude, non contesté par Anthony. C reste possible plus tard si le coût devient le vrai sujet.

## Décisions d'Anthony

- Les modèles **débattent**, **Anthony tranche**.
- GPT branché via **Codex ou un MCP** (installation à valider).
- Agents spécialisés : front **React**, back **C#**, **Node.js**, **Rust**, image, vidéo, revue de code (image/vidéo → chantier 3).
- Le cycle ne s'arrête **que quand les modèles ne sont pas d'accord**.

## La conception

### 1. Pont GPT

- Installer le CLI Codex (accord requis), connexion avec le compte ChatGPT (`codex login`), sans clé API.
- Appel : `codex exec --sandbox read-only` lancé dans le dossier du projet ; GPT peut lire le code mais pas l'écrire.
- Tours suivants d'un débat : `codex exec resume <session>` pour garder le fil.
- Un petit script `~/.claude/skills/debate/gpt.sh` encapsule l'appel (prompt en entrée, réponse en sortie, id de session conservé) pour que tous les agents l'appellent de la même façon.
- Vérifier au démarrage que Codex est installé et connecté ; sinon le débat se dégrade en « Claude seul » **et le dit** dans la synthèse.

### 2. Protocole `/debate`

Entrée : une question + des fichiers de contexte. Utilisable à la main (`/debate <question>`) et appelé automatiquement par le cycle.

1. **Tour 0, en aveugle** : un sous-agent Claude (Opus par défaut) et GPT reçoivent le même brief et répondent chacun sans voir l'autre. Format imposé : position, arguments, niveau de confiance, ce qui ferait changer d'avis.
2. **Tour 1** : chacun reçoit la réponse de l'autre, doit lister ce qu'il concède, ce qu'il conteste et pourquoi, puis donner sa position révisée. Consigne explicite contre la complaisance : « ne concède que ce que tu peux justifier ».
3. **Tour 2** seulement s'il reste un désaccord.
4. **Synthèse** par l'orchestrateur : `ACCORD` ou `DÉSACCORD`, tableau des points d'accord, des divergences avec les meilleurs arguments de chaque côté. L'orchestrateur ne tranche pas un désaccord.
5. Trace écrite dans le projet : `.superpowers/debates/AAAA-MM-JJ-<sujet>.md`.

### 3. L'équipe (`~/.claude/agents/`)

| Agent | Modèle | Outils / skills | Rôle |
|---|---|---|---|
| (session principale) orchestrateur | Fable | tous | Pilote le cycle, brainstorme, découpe, lance les débats |
| challenger | Sonnet → GPT | Bash (gpt.sh), Read | Relaie un brief vers GPT et renvoie sa réponse brute |
| product-owner | Fable | skills `epic-hypothesis`, `prioritization-advisor` | Transforme une idée en hypothèse testable, challengée par `/debate` |
| front-react | Sonnet | `vercel-react-best-practices`, `impeccable` | Front React |
| back-csharp | Sonnet | `dotnet-webapi`, `optimizing-ef-core-queries` | ASP.NET / EF Core |
| back-node | Sonnet | - | Node / TypeScript |
| back-python | Sonnet | - | Python (scripts, CLI, services) |
| back-rust | Opus | - | Rust (plus d'erreurs des modèles sur l'emprunt/les durées de vie) |
| test-writer | Sonnet | - | Tests d'abord, comme Orbital |
| reviewer | Opus, lecture seule | `code-review`, `ponytail-audit` | Revue Claude ; tourne en parallèle d'une revue GPT |
| security | Opus, lecture seule | `owasp-security`, `differential-review` | Changements sensibles (auth, données, crypto) |
| qa | Sonnet | Playwright | Teste l'appli comme un humain, captures |
| doc-writer | Sonnet → DeepSeek flash | `documentation-writer` | README, docs |

Le choix des modèles par rôle est un **[choix de Claude]** à ajuster à l'usage.

### 4. Le cycle

```
idée → product-owner <-> /debate → spec
     → plan (superpowers:writing-plans) <-> /debate
     → test-writer → front/back-xx (mécanique → DeepSeek, règles DS)
     → tests verts → revue Opus en parallèle de revue GPT (+ security si sensible, + qa si UI)
     → fusion locale → [STOP] AVANT PUSH (toujours)
À chaque /debate : ACCORD → on continue, tracé ; DÉSACCORD → [STOP] Anthony tranche
```

- S'appuie sur superpowers (brainstorming, writing-plans, subagent-driven-development) plutôt que de refaire un orchestrateur. La valeur ajoutée est l'insertion des `/debate` aux trois points : spec, plan, revue.
- Revue : les deux relecteurs rendent `APPROVE` / `REQUEST_CHANGES` + points. Même verdict → continue ; verdicts différents → débat 2 tours → si toujours différent, arrêt.
- Boucle de correction : 2 tours de `REQUEST_CHANGES` concordants max, puis arrêt (règle d'Orbital).
- Journal `progress.md` façon crushed : « Décision : … - coût si faux : … » pour chaque accord automatique, pour qu'Anthony puisse relire ce qui s'est décidé sans lui.

### 5. Routage des coûts

- Règles DeepSeek d'Orbital (`rules/deepseek.md`) déplacées en règle globale référencée par les agents, avec la leçon de bricktales : **DeepSeek seulement pour les tâches à faible contexte** (traductions, CRUD isolé, docs, résumés de tests, scans en lecture seule). Jamais : auth, isolation des données, crypto, architecture, revue finale.
- Le débat ne tourne qu'aux trois points du cycle et sur demande, pas sur chaque tâche.

## Décisions complémentaires (issues de la relecture)

- **[choix de Claude] Quota GPT épuisé ou Codex indisponible** : le cycle continue avec Claude seul, le signale dans la synthèse et dans `progress.md`, sans s'arrêter.
- **[choix de Claude] Revue double par branche, pas par tâche** : le relecteur Claude relit chaque tâche (comme aujourd'hui avec superpowers) ; la revue GPT + débat éventuel a lieu une fois sur le diff complet de la branche, avant la fusion. Limite le coût et les arrêts.
- **[choix de Claude] Skill `delegate-to-deepseek`** : elle est modifiée pour suivre la règle « faible contexte uniquement » et la liste « jamais délégué », au lieu de coexister avec une règle contradictoire.
- **[choix de Claude] Projets qui ont leurs propres agents** (Orbital…) : le cycle utilise les agents du projet quand ils existent (ils sont prioritaires et adaptés), les agents globaux sinon. Format de verdict commun `VERDICT: APPROVE | REQUEST_CHANGES`, déjà celui d'Orbital.
- **[choix de Claude] Traces** : `progress.md` et les débats vont dans `.superpowers/` du projet, ignoré par git (comme dans crushed). Les décisions qui comptent sont reprises dans la spec ou la description de PR.
- **[choix de Claude] Disponibilité de Codex avec l'abonnement ChatGPT** : vérifiée à l'installation ; si non disponible, on revient sur l'option B (MCP + clé API) avant d'aller plus loin.

## Décisions finales d'Anthony (2026-11-27)

- **Secrets : blocage réel.** GPT (Codex) et DeepSeek travaillent sur une copie filtrée du projet : uniquement les fichiers suivis par git (`git ls-files`), en excluant `.env*`, clés (`*.pem`, `*.key`, `id_*`), fichiers de credentials et tout motif listé dans un `.aiignore` optionnel du projet. Grok ne reçoit que le texte du prompt, jamais de fichiers.
- **Brainstorming : Anthony participe et valide la spec.** Ensuite plan, tests, code et revue tournent seuls ; arrêts uniquement sur désaccord Claude/GPT et avant tout `git push`.
- **`/verify` en plus de `/debate`** : lancé à la main, envoie la dernière réponse ou production de Claude à GPT pour une contre-vérification en un tour (erreurs factuelles, API inventées, raisonnement faux). Si GPT trouve un problème, Claude répond point par point ; si le désaccord persiste, proposer `/debate`.
- **Commandes en anglais** : `/debate`, `/verify`, `/grok`.

## Grok (xAI)

- Demande d'Anthony : utiliser Grok pour les tâches ou prompts que Claude ou ChatGPT refusent ou ne savent pas faire.
- Accès : clé API xAI (Anthony crée le compte). La clé est lue depuis la variable d'environnement `XAI_API_KEY`, jamais écrite dans un fichier versionné ni collée dans la conversation.
- **[choix de Claude] Appel explicite uniquement** (`/grok <tâche>` ou agent `grok` nommé), pas de bascule automatique sur refus. Usages visés : fiction sombre ou violente, satire, humour cru, visuels refusés par excès de prudence, actualité et tendances X (utile au chantier 3).
- Pont : petit script appelant l'API xAI (compatible OpenAI) en Python stdlib, sur le modèle de `gpt.sh`. Mêmes règles de confidentialité : aucun secret ni fichier sensible envoyé.
- Forfait ChatGPT d'Anthony : **Plus**, qui inclut Codex → pont GPT via `codex login` confirmé possible ; quota limité, d'où la revue GPT une fois par branche.

## Laissé au constructeur

- Texte exact des prompts des agents et du débat, format précis des fichiers de trace.
- Choix entre skill et commande pour `/debate` et pour lancer le cycle.
- Organisation interne de `gpt.sh` (gestion des id de session, délais, erreurs).
- Comment référencer la règle DeepSeek globale depuis les agents.

## Skills : qui les utilise et quand

Demande d'Anthony : utiliser **tous** les skills installés, au bon moment. Mécanisme : le champ `skills:` du frontmatter des agents précharge les skills de l'agent ; une table de routage globale (`rules/skills.md`, référencée depuis `CLAUDE.md`) dit à l'orchestrateur quel skill déclencher à quelle phase. Origines : plugins (marketplaces), `~/.agents/skills` (liens symboliques, installés par l'outil `skills`), dossiers copiés dans `~/.claude/skills`.

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

**[choix de Claude]** Les skills Atlassian et LSP ne sont pas branchés sur des agents : ils servent dans des contextes précis (pro, C/Swift) et se déclenchent déjà seuls.

## Portabilité sur une autre machine

Demande d'Anthony : pouvoir tout réinstaller ailleurs.

- **[choix de Claude] Un repo GitHub privé `claude-setup`** (compte perso), organisé en **plugin Claude Code + marketplace** : agents, skills `/debate` `/verify` `/grok`, scripts (`gpt.sh`, pont xAI, copie filtrée), règles (`rules/deepseek.md`, `rules/skills.md`). Sur une nouvelle machine : `/plugin marketplace add <compte>/claude-setup` puis installation du plugin.
- **`bootstrap.sh`** dans le repo, pour ce qu'un plugin ne transporte pas, avec accord avant chaque installation :
  - réinstalle les plugins listés dans un manifeste (ceux de `settings.json` : superpowers, ponytail, context-mode, ui-ux-pro-max…) ;
  - réinstalle les skills tiers depuis leurs sources (manifeste avec l'origine de chaque skill) ;
  - installe Codex CLI, puis lance `codex login` ;
  - installe le serveur MCP DeepSeek (`~/Dev/mcp/deepseek-as-subagent`) ;
  - vérifie `XAI_API_KEY`, `COMFYUI_URL` et la connexion à DeepSeek, sans afficher de valeurs.
- **Ne voyage pas** : clés et sessions (`codex login`, `XAI_API_KEY`, config DeepSeek), historique et mémoire de `~/.claude`. Chaque machine les refait.
- Écarté : versionner `~/.claude` en entier (historique, caches, risque de secrets) ; dotfiles avec liens symboliques (moins standard qu'un plugin).
