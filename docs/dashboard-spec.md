# /dashboard - conception courte

Date : 2026-11-27 - validée par Anthony.

## Intention

Une commande `/dashboard` dans ai-team qui ouvre le tableau de suivi du projet courant, comme celui d'Orbital, utilisable dans tous les projets. Un tableau (artifact claude.ai privé) par projet.

## Approches

- **Retenue : reprendre le tableau d'Orbital en version commune** (collecteur Python stdlib + page + artifact avec base de données). Déjà rodé dans Orbital, OrbitalInvest et bowtrail.
- Écartée : page HTML locale ouverte dans le navigateur (perd le lien privé partageable et le modèle existant).
- Écartée : un tableau unique pour tous les projets (choix d'Anthony : un par projet).

## Conception

- `bin/dashboard_collect.py` : collecteur repris de `~/Dev/Orbital/scripts/dashboard/collect.py`, avec ses tests. Repo GitHub lu depuis `git remote`, slug des journaux Claude Code déduit du chemin du projet, rien en dur. Ajouts : appels GPT et Grok, débats (nombre, accords, désaccords, lus dans la ligne `RESULT:` des fichiers `.superpowers/debates/*.md`).
- `gpt.py` et `grok.py` ajoutent une ligne de compteurs par appel dans `~/.ai-team/usage.log` : date, projet, modèle, ok/échec, durée, tokens si Codex les donne. Aucun contenu.
- `dashboard/dashboard.html` : page reprise d'Orbital, plus une section « Modèles » (part Claude / GPT / DeepSeek / Grok).
- `/dashboard` : premier lancement : crée l'artifact du projet et écrit son adresse dans `<projet>/docs/dashboard/config.json` (versionné). Ensuite : collecteur, puis écriture des chiffres dans la base de l'artifact (`board/latest`, `events/<horodatage-sujet>`), sans republier la page. Ouvre le tableau.
- `/cycle` rafraîchit le tableau en fin de tâche, à chaque porte et en fin de cycle.

## Contraintes

- Tableaux existants d'Orbital, OrbitalInvest et bowtrail inchangés.
- Compteurs seulement : jamais de contenu d'échange, de secrets, de données personnelles (DASH-05 d'Orbital). Aucun chiffre inventé.
- Écriture dans la base réservée au propriétaire, lecture pour les personnes ayant accès.
- `gh` avec le bon compte : `GH_TOKEN=$(gh auth token -u <compte>)`, compte choisi selon les règles du CLAUDE.md global.
- Pas de tiret cadratin, point médian ni emoji.

## Laissé au constructeur

Mise en page exacte de la section « Modèles », format exact de `usage.log`, noms des clés de la base au-delà de `board/latest` et `events/*`.

## Ajout : agents en direct et carte animée du cycle (demande d'Anthony)

- **Agents en direct** : pour chaque sous-agent, son type (`front-react`, `reviewer`...), son modèle, son état (fiche `.meta.json` : champ `finished`, à défaut écriture il y a moins de 2 min), le libellé court de sa tâche (champ `description` de la fiche, 3 à 5 mots, tronqué à 60 caractères) et le nom du dernier outil utilisé (`Edit`, `Bash`...). **[choix de Claude]** Le libellé court est un intitulé de tâche, pas un contenu d'échange : il est affiché, contrairement au choix d'Orbital. Les prompts, réponses et arguments d'outils restent exclus.
- **Étape du cycle** : `/cycle` écrit `.superpowers/cycle.json` (`{"phase", "task", "updatedAt"}`) à chaque changement d'étape. Phases : `idea`, `spec`, `plan`, `tests`, `build`, `review`, `merge`, `push`.
- **Carte animée** : schéma SVG du cycle (idée, spec, plan, tests, code, revue Claude en parallèle de GPT, fusion, push) avec l'étape en cours mise en avant, les liens animés vers l'étape suivante, les agents actifs affichés sur l'étape où ils travaillent (avec modèle et libellé), les débats en cours sur les portes spec, plan et revue (accord ou désaccord). Les mouvements respectent `prefers-reduced-motion`.
