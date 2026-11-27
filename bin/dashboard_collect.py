"""Collecte les indicateurs du tableau de suivi du projet (rules/dashboard.md, DASH-02).

Sortie : le document JSON `board/latest` de l'artifact (stdout).
Sources : journaux Claude Code du projet (~/.claude/projects/<slug>), git, gh, docs/dashboard/plans.json,
registres d'avancement (docs/superpowers/plans/*.progress.md versionné et registre SDD .superpowers/sdd/<plan>/progress.md),
compteurs du MCP deepseek (~/.deepseek-mcp/usage.log, tous projets confondus).
Seuls des compteurs sont lus (modèle, tokens, dates), jamais le contenu des échanges (DASH-05).
Toutes les lectures et les commandes passent par load_sources() (chemins et exécutables injectables) ;
build_board(sources) est pur : il ne lit que le dict fourni et ne fait aucune E/S.
Usage : GH_TOKEN=$(gh auth token -u <compte>) python3 -I scripts/dashboard/collect.py [--repo <propriétaire/dépôt>] [--project-slug <slug>] [--root <racine locale>]
"""
import argparse
import copy
import datetime as dt
import glob
import json
import os
import re
import subprocess
import time

GITHUB_REMOTE = re.compile(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?/?$")


def repo_from_remote(url):
    """« propriétaire/dépôt » depuis l'URL du remote git, None si ce n'est pas GitHub."""
    m = GITHUB_REMOTE.search((url or "").strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def slug_for(path):
    """Nom du dossier des journaux Claude Code : tout caractère non alphanumérique devient « - »."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)
PLATFORMS = {"cli": "Claude Code CLI", "sdk-py": "Agent SDK (Python)", "sdk-ts": "Agent SDK (TS)", "claude-desktop": "Claude Desktop"}
# état de la page ← état du registre (« Task N: complete » → done, « impl » → review, « tests » → in_progress)
ETATS = {"complete": "done", "impl": "review", "tests": "in_progress"}
# rang d'un état : entre registres, le plus avancé gagne ; jamais de régression (complete puis impl reste done)
RANG = {"todo": 0, "in_progress": 1, "review": 2, "done": 3}


def sh(args, cwd):
    """Commande externe : sortie vide si elle échoue, jamais d'exception."""
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60, check=True).stdout
    except (subprocess.SubprocessError, OSError):
        return ""


def usage_rows(path, agent_type=None):
    """Une ligne par réponse de l'API (dédupliquée : un message peut être écrit en plusieurs blocs).
    Rôle : le type du sous-agent (frontend, reviewer…) quand le journal a sa fiche .meta.json.
    Seuls model, usage et timestamp sont lus : le contenu des messages n'est jamais copié.
    Une ligne JSON invalide est ignorée sans casser le comptage."""
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict) or not m.get("usage"):
                continue
            if m.get("model") == "<synthetic>":  # messages fabriqués par Claude Code, sans appel au modèle
                continue
            u = m["usage"]
            rows[(m.get("id"), d.get("requestId"))] = {
                "model": m.get("model") or "inconnu",
                "platform": PLATFORMS.get(d.get("entrypoint"), d.get("entrypoint") or "inconnue"),
                "role": agent_type or ("sous-agent" if d.get("isSidechain") else "session principale"),
                "input": u.get("input_tokens", 0),
                "output": u.get("output_tokens", 0),
                "cacheWrite": u.get("cache_creation_input_tokens", 0),
                "cacheRead": u.get("cache_read_input_tokens", 0),
                "at": d.get("timestamp"),
            }
    return list(rows.values())


def total(r):
    return r["input"] + r["output"] + r["cacheWrite"] + r["cacheRead"]


def group(rows, key):
    out = {}
    for r in rows:
        g = out.setdefault(r[key], {"name": r[key], "responses": 0, "input": 0, "output": 0, "cacheWrite": 0, "cacheRead": 0})
        g["responses"] += 1
        for k in ("input", "output", "cacheWrite", "cacheRead"):
            g[k] += r[k]
    for g in out.values():
        g["total"] = total(g)
        g["withoutCacheReads"] = g["total"] - g["cacheRead"]
    return sorted(out.values(), key=lambda g: -g["total"])


def by_day(rows):
    days = {}
    for r in rows:
        if r["at"]:
            days[r["at"][:10]] = days.get(r["at"][:10], 0) + total(r)
    # objets et non paires : la base de l'artifact refuse les tableaux imbriqués
    return [{"day": d, "total": n} for d, n in sorted(days.items())]


def claude_vs_deepseek(tokens_claude, tokens_deepseek):
    """Part DeepSeek dans le total des jetons (objectif : préserver le quota Claude, DS-01)."""
    somme = tokens_claude + tokens_deepseek
    return {"claude": tokens_claude, "deepseek": tokens_deepseek,
            "deepseekShare": round(tokens_deepseek / somme, 3) if somme else 0.0}


def deepseek(usage_texte, log_texte):
    """Compteurs du MCP deepseek ← contenus de usage.log et de server.log ("" s'ils sont absents).
    usage.log : une ligne par délégation, « … tokens=<n> ». server.log associe
    « job started: <id> model=<m> » à « job <id> completed … tokens=<n> » pour la répartition par modèle."""
    if not usage_texte:
        return {"available": False, "delegations": 0, "tokens": 0, "byModel": []}
    n, tok = 0, 0
    for line in usage_texte.splitlines():
        m = re.search(r"tokens=\s*(\d+)", line)
        if m:
            n += 1
            tok += int(m.group(1))
    started, models = {}, {}
    for line in log_texte.splitlines():
        if m := re.search(r"job started: (\w+) model=(\w+)", line):
            started[m.group(1)] = m.group(2)
        elif (m := re.search(r"job (\w+) completed\..*tokens=(\d+)", line)) and m.group(1) in started:
            g = models.setdefault(started[m.group(1)], {"responses": 0, "total": 0})
            g["responses"] += 1
            g["total"] += int(m.group(2))
    # shortcut: seuls les jobs en arrière-plan journalisent leur modèle, les délégations synchrones restent dans « tokens » sans ventilation ; ventiler dès que le journal DeepSeek donne le modèle des délégations synchrones.
    by_model = [{"name": "DeepSeek " + k.capitalize(), **v} for k, v in sorted(models.items(), key=lambda kv: -kv[1]["total"])]
    return {"available": True, "delegations": n, "tokens": tok, "byModel": by_model}


def etats_registre(texte):
    """Un registre d'avancement → {N: état} des tâches qui y sont suivies.
    - « Task N: tests … » → in_progress, « Task N: impl … » → review, « Task N: complete … » → done ;
    - « Task N: fix round R/5 … », « Task N: minor (deferred): … », « Task N: Ruling: … », « Task N: parked … »
      sont du bruit : ils ne changent pas l'état et n'inventent pas de tâche ;
    - dans un même fichier, le rang le plus avancé l'emporte (« complete » puis « impl » reste done).
    Seul l'état est retenu : le texte qui suit la ligne n'est jamais copié (DASH-05)."""
    etats = {}
    for ligne in texte.splitlines():
        m = re.match(r"\s*Task (\d+)\s*:\s*(tests|impl|complete)\b", ligne, re.I)
        if not m:
            continue
        n, etat = m.group(1), ETATS[m.group(2).lower()]
        if RANG[etat] > RANG.get(etats.get(n), 0):
            etats[n] = etat
    return etats


def pr_ids(texte):
    """PR référencées dans un registre : « Task N: complete (commits a..b, review clean, PR #39 → b0da75e) » → {N: 39}."""
    out = {}
    for ligne in texte.splitlines():
        m = re.match(r"\s*Task (\d+)\s*:\s*complete\b.*?PR #(\d+)", ligne, re.I)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def duree(run):
    """Durée d'un run GitHub Actions (createdAt → updatedAt)."""
    try:
        a, b = (dt.datetime.fromisoformat(run[k].replace("Z", "+00:00")) for k in ("createdAt", "updatedAt"))
    except (KeyError, TypeError, ValueError):
        return 0
    return round((b - a).total_seconds() / 60, 1)


def github(gh, repo, kind, champs):
    """`gh` avec l'environnement courant (GH_TOKEN fourni par l'appelant). Échec → (liste vide, message français)."""
    if kind == "runs":
        args = [gh, "run", "list", "--repo", repo, "--limit", "100", "--json", champs]
    else:
        args = [gh, "pr", "list", "--repo", repo, "--state", "all", "--limit", "100", "--json", champs]
    quoi = "les runs de CI" if kind == "runs" else "les pull requests"
    sortie = sh(args, None)
    if not sortie:
        return [], f"GitHub injoignable ({quoi}) : gh a échoué, listes vides (GH_TOKEN fourni ?)"
    try:
        donnees = json.loads(sortie)
    except ValueError:
        return [], f"Réponse GitHub illisible ({quoi}) : listes vides"
    if not isinstance(donnees, list):
        return [], f"Réponse GitHub inattendue ({quoi}) : listes vides"
    return donnees, None


def worktrees(porcelain, dirty):
    """Worktrees ← `git worktree list --porcelain` : branche, HEAD, modifié ou non
    (le chemin est retiré : il contient le nom d'utilisateur). `dirty` = fonction (chemin → sortie git status)."""
    out, wt = [], {}
    for line in porcelain.splitlines() + [""]:
        if not line and wt:
            out.append(wt)
            wt = {}
        elif line.startswith("worktree "):
            wt = {"path": line[9:], "head": None, "branch": None}
        elif line.startswith("HEAD "):
            wt["head"] = line[5:12]
        elif line.startswith("branch "):
            wt["branch"] = line[7:].removeprefix("refs/heads/")
    for w in out:
        w["dirty"] = bool((dirty(w.pop("path")) or "").strip())
    return out


def prochain_plan(plans):
    """Le plan en cours : statut in_progress, à défaut le premier non commencé."""
    return next((p for p in plans if p.get("status") == "in_progress"), None) or \
        next((p for p in plans if p.get("status") == "not_started"), None)


def fusion(etats, n, etat):
    """Inscrit un état sans jamais régresser : le rang le plus avancé gagne."""
    if RANG[etat] > RANG.get(etats.get(n), 0):
        etats[n] = etat


def etats_fusionnes(registres):
    """États de toutes les tâches, registres fusionnés : par tâche, l'état de rang maximal gagne
    (todo < in_progress < review < done), quel que soit le fichier ou l'ordre de lecture."""
    etats = {}
    for texte in registres:
        for n, etat in etats_registre(texte).items():
            fusion(etats, n, etat)
    return etats


def taches(registres, heads):
    """Tâches du plan en cours : titres lus dans le plan (### Task N: …), état déduit des registres.
    `heads` = [(N, titre)], None si aucun plan en cours. La PR vient de la première ligne « Task N: complete »
    qui en cite une (registre versionné d'abord, puis registre SDD)."""
    if heads is None:
        return None
    etats = etats_fusionnes(registres)
    prs = {}
    for texte in registres:
        for n, pr in pr_ids(texte).items():
            prs.setdefault(n, pr)
    out = []
    for n, titre in heads:
        t = {"id": n, "title": titre.replace("`", "").strip(), "state": etats.get(n, "todo")}
        if n in prs:
            t["pr"] = prs[n]
        out.append(t)
    return out


def avancement(plans, registres, total_taches):
    """tasksDone / tasksTotal d'un plan versionné (### Task N dans son plan, états dans ses registres) ;
    un plan sans fichier ou sans section « ### Task N » garde les chiffres de plans.json."""
    for plan in plans:
        numeros = (total_taches or {}).get(plan.get("id"))
        if not numeros:
            continue
        etats = etats_fusionnes((registres or {}).get(plan.get("id")) or [])
        plan["tasksTotal"] = len(numeros)
        # Seuls les numéros des titres « ### Task N » comptent : un registre peut en nommer d'autres (3a, 3b…).
        plan["tasksDone"] = sum(1 for n in numeros if etats.get(n) == "done")


def agents(transcriptions):
    """Sous-agents, à partir des transcriptions déjà lues par load_sources() : type d'agent, modèle,
    état actif/inactif, compteurs, date de début. Jamais la description libre des fiches .meta.json (DASH-05)."""
    out = []
    for t in transcriptions:
        rows = t.get("rows") or []
        out.append({
            "type": t.get("agentType"),
            "model": sorted({r["model"] for r in rows}) or ([t["model"]] if t.get("model") else []),
            "tokens": sum(total(r) for r in rows),
            "responses": len(rows),
            # shortcut: « actif » = transcription écrite il y a moins de 2 min, faute de statut officiel ; lire ce statut dès que Claude Code l'expose.
            "status": "actif" if t.get("mtime") and time.time() - t["mtime"] < 120 else "terminé",
            "startedAt": min((r["at"] for r in rows if r["at"]), default=None),
        })
    out.sort(key=lambda a: a["startedAt"] or "", reverse=True)
    return out


def alerts(prs, plans, registres, lectures, non_suivis, deepseek_log):
    """Ce qui demande l'attention du propriétaire : seulement des faits vérifiables, rien d'estimé.
    `non_suivis` = sortie de `git status --porcelain` (seul le COMPTE des « ?? » est publié, jamais les noms),
    `deepseek_log` = contenu de ~/.deepseek-mcp/server.log ("" s'il est absent)."""
    out = list(lectures)
    nb = sum(1 for line in non_suivis.splitlines() if line.startswith("??"))
    if nb:
        out.append({"level": "warn", "text": f"{nb} fichier(s) non suivi(s) dans le dépôt"})
    now = dt.datetime.now()
    for line in deepseek_log.splitlines():
        if "job failed" in line:
            try:
                at = dt.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if now - at < dt.timedelta(hours=6):  # shortcut: fenêtre fixe de 6 h, un échec traité sort seul de la liste ; passer à un acquittement explicite si un échec doit rester visible plus longtemps.
                out.append({"level": "bad", "text": f"Job DeepSeek en échec le {at:%d/%m à %H:%M}"})
    utc = dt.datetime.now(dt.timezone.utc)
    for pr in prs:
        if pr.get("state") == "OPEN" and pr.get("createdAt"):
            try:
                age = utc - dt.datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
            except ValueError:
                continue
            if age > dt.timedelta(hours=24):
                out.append({"level": "warn", "text": f"PR #{pr['number']} ouverte depuis {age.days or 1} j"})
    for plan in plans:
        for texte in (registres or {}).get(plan.get("id")) or []:
            for line in texte.splitlines():
                m = re.match(r"(\S+) review R(\d+)", line)
                if m and int(m.group(2)) >= 3:
                    out.append({"level": "bad", "text": f"{m.group(1)} : revue au tour {m.group(2)} (escalade au-delà de 2)"})
    return out


def todo(texte):
    """Actions qui reviennent au propriétaire : section « Avant la mise en ligne » de docs/STATUS.md."""
    m = re.search(r"^## Avant la mise en ligne\n(.*?)(?=^## |\Z)", texte or "", re.M | re.S)
    items = re.findall(r"^- (.+)$", m.group(1), re.M) if m else []
    return [re.sub(r"\*\*|`", "", i) for i in items]


def build_board(sources):
    """Sources lues → document JSON du tableau. Aucune E/S : ne lit que le dict `sources` fourni.
    Le résultat ne contient que des compteurs, des titres et des états : jamais le contenu des échanges (DASH-05)."""
    plans = [p for p in copy.deepcopy(sources.get("plans") or []) if isinstance(p, dict)]
    regs = sources.get("registres") or {}
    transcriptions = sources.get("transcriptions") or []
    avancement(plans, regs, sources.get("total_taches"))
    all_rows = [r for t in transcriptions for r in t.get("rows") or []]
    ds = deepseek(sources.get("usage_texte") or "", sources.get("deepseek_log") or "")
    runs = sources.get("runs") or []
    prs = sources.get("prs") or []
    registres = [texte for textes in regs.values() for texte in textes]
    courant = prochain_plan(plans)
    current = None
    if courant is not None:
        current = {"plan": f"{courant['id']} {courant['title']}", "tasks": taches(registres, sources.get("taches_courantes"))}
    tokens_total = sum(total(r) for r in all_rows)
    cache_reads = sum(r["cacheRead"] for r in all_rows)
    return {
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "repo": sources.get("repo_gh"),
        "plans": plans,
        "worktrees": sources.get("worktrees") or [],
        "agents": agents([t for t in transcriptions if t.get("isAgent")]),
        "jobs": runs[:15],
        "ci": {"runs": len(runs), "minutes": round(sum(r.get("minutes", 0) for r in runs), 1)},
        "prs": prs,
        "current": current,
        "alerts": alerts(prs, plans, regs, (sources.get("alerts_sources") or []) + (
                             [] if sources.get("repo_gh") else
                             [{"level": "warn", "text": "Pas de dépôt GitHub : PR et CI non suivies."}]),
                         sources.get("journal_git_status") or "", sources.get("deepseek_log") or ""),
        "todo": sources.get("todo") or [],
        "deepseek": ds,
        "tokens": {
            "total": tokens_total,
            "withoutCacheReads": tokens_total - cache_reads,
            "requests": len(all_rows),
            "byModel": group(all_rows, "model"),
            "byPlatform": group(all_rows, "platform"),
            "byRole": group(all_rows, "role"),
            "byDay": by_day(all_rows),
            "claudeVsDeepseek": claude_vs_deepseek(tokens_total, ds.get("tokens") or 0),
        },
    }


def lire(chemin):
    """Contenu d'un fichier texte ; "" s'il est absent ou illisible."""
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def fichiers_jsonl(projet):
    """Transcriptions *.jsonl d'un dossier de projet Claude Code (liste vide si le dossier manque)."""
    return sorted(set(glob.glob(os.path.join(projet, "**", "*.jsonl"), recursive=True))) if projet else []


def transcription(path):
    """Une transcription lue : type d'agent et modèle (fiche .meta.json, jamais sa description), date d'écriture,
    compteurs. Seuls model, usage et timestamp sont retenus, jamais le contenu des messages (DASH-05)."""
    agent_type, modele = None, None
    meta_path = path[: -len(".jsonl")] + ".meta.json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f) or {}
            agent_type, modele = meta.get("agentType"), meta.get("model")
        except (OSError, ValueError, AttributeError):
            agent_type, modele = None, None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None
    return {"agentType": agent_type, "model": modele, "mtime": mtime,
            "isAgent": os.path.basename(path).startswith("agent-"), "rows": usage_rows(path, agent_type)}


def registre_sdd(plan):
    """Chemin relatif du registre SDD d'un plan : `.superpowers/sdd/<nom du fichier de plan sans extension>/progress.md`
    (« docs/superpowers/plans/2026-10-17-socle-technique.md » → `.superpowers/sdd/2026-10-17-socle-technique/…`).
    Le dossier porte le nom du fichier de plan, pas l'identifiant du plan ; None sans planFile."""
    plan_file = plan.get("planFile")
    if not plan_file:
        return None
    return os.path.join(".superpowers/sdd", os.path.splitext(os.path.basename(plan_file))[0], "progress.md")


def registres(repo, plans):
    """Contenus des registres d'avancement du dépôt local, par identifiant de plan (ordre de lecture) :
    le registre versionné (progressFile), puis le registre SDD (registre_sdd) s'il existe.
    Les deux sont fusionnés par état le plus avancé : aucun des deux ne fait foi seul."""
    out = {}
    for plan in plans:
        textes = []
        for rel in (plan.get("progressFile"), registre_sdd(plan)):
            texte = lire(os.path.join(repo, rel)) if rel else ""
            if texte:
                textes.append(texte)
        out[plan.get("id")] = textes
    return out


def taches_plan(repo, plans):
    """Titres des tâches du plan en cours (### Task N: …) et nombre de tâches de chaque plan versionné.
    Rend (heads, total) ; heads vaut None s'il n'y a aucun plan en cours."""
    courant = prochain_plan(plans)
    heads, total = None, {}
    for plan in plans:
        if not plan.get("planFile"):
            continue
        trouvees = re.findall(r"^### Task (\d+): (.+)$", lire(os.path.join(repo, plan["planFile"])), re.M)
        total[plan.get("id")] = [n for n, _ in trouvees]
        if plan is courant:
            heads = trouvees
    return heads, total


def discover_plans(repo):
    """Plans déduits de docs/superpowers/plans/*.md quand docs/dashboard/plans.json n'existe pas."""
    plans = []
    for path in sorted(glob.glob(os.path.join(repo, "docs/superpowers/plans/*.md"))):
        if path.endswith(".progress.md"):
            continue
        texte = lire(path)
        titre = re.search(r"^# (.+)$", texte, re.M)
        rel = os.path.relpath(path, repo)
        plans.append({
            "id": os.path.basename(path)[:-3],
            "title": titre.group(1).strip() if titre else os.path.basename(path)[:-3],
            "status": "todo",
            "tasksDone": 0,
            "tasksTotal": len(re.findall(r"^### Task \d+", texte, re.M)),
            "pr": None,
            "planFile": rel,
            "progressFile": rel[:-3] + ".progress.md",
        })
    return plans


def load_sources(repo, projet, usage_path, repo_gh=None, plans_file=None, gh=None, git=None, deepseek_log_path=None):
    """Lit TOUTES les sources (journalisation Claude Code, registres, plans, STATUS.md, git, gh, journaux DeepSeek)
    et rend un dict lisible par build_board().
    `repo` = racine du dépôt en local ; `repo_gh` = « propriétaire/dépôt » pour gh (None : pas de suivi GitHub) ;
    `gh` et `git` = chemins des exécutables (défaut : ceux du PATH) ; `usage_path` et `deepseek_log_path` =
    journaux DeepSeek (usage.log ; server.log, défaut ~/.deepseek-mcp/server.log). Un gh introuvable ne lève pas :
    les listes sont vides et une alerte « warn » en français est posée."""
    gh, git = gh or "gh", git or "git"
    try:
        with open(plans_file or os.path.join(repo, "docs/dashboard/plans.json"), encoding="utf-8") as f:
            plans = json.load(f)
    except (OSError, ValueError):
        plans = []
    plans = [p for p in plans if isinstance(p, dict)] if isinstance(plans, list) else []
    plans = plans or discover_plans(repo)
    runs, alerte_runs, prs, alerte_prs = [], None, [], None
    if repo_gh:
        runs, alerte_runs = github(gh, repo_gh, "runs", "databaseId,displayTitle,headBranch,status,conclusion,createdAt,updatedAt,url")
        prs, alerte_prs = github(gh, repo_gh, "prs", "number,title,state,headRefName,url,mergedAt,createdAt,isDraft")
    for r in runs:
        r["minutes"] = duree(r)
    heads, total = taches_plan(repo, plans)
    return {
        "repo_gh": repo_gh,
        "journal_git_status": sh([git, "status", "--porcelain"], repo),
        "transcriptions": [transcription(p) for p in fichiers_jsonl(projet)],
        "usage_texte": lire(usage_path) if usage_path else "",
        "deepseek_log": lire(os.path.expanduser(deepseek_log_path or "~/.deepseek-mcp/server.log")),
        "plans": plans,
        "registres": registres(repo, plans),
        "taches_courantes": heads,
        "total_taches": total,
        "runs": runs,
        "prs": prs,
        "worktrees": worktrees(sh([git, "worktree", "list", "--porcelain"], repo),
                               lambda chemin: sh([git, "status", "--porcelain"], chemin)),
        "todo": todo(lire(os.path.join(repo, "docs/STATUS.md"))),
        "alerts_sources": [{"level": "warn", "text": t} for t in (alerte_runs, alerte_prs) if t],
    }


def main():
    p = argparse.ArgumentParser(description="Collecte les indicateurs du tableau de suivi (board/latest).")
    p.add_argument("--root", default=os.getcwd(), help="dossier du projet (défaut : dossier courant)")
    p.add_argument("--repo", help="dépôt GitHub « propriétaire/dépôt » (défaut : lu dans le remote origin)")
    p.add_argument("--project-slug", help="slug du projet dans ~/.claude/projects/ (défaut : déduit du chemin)")
    args = p.parse_args()
    racine = os.path.abspath(os.path.expanduser(args.root))
    racine = sh(["git", "rev-parse", "--show-toplevel"], racine).strip() or racine
    repo_gh = args.repo or repo_from_remote(sh(["git", "remote", "get-url", "origin"], racine))
    projet = os.path.expanduser("~/.claude/projects/" + (args.project_slug or slug_for(racine)))
    sources = load_sources(racine, projet, os.path.expanduser("~/.deepseek-mcp/usage.log"), repo_gh=repo_gh)
    print(json.dumps(build_board(sources), ensure_ascii=False))


if __name__ == "__main__":
    main()
