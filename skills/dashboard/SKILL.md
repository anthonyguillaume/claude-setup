---
name: dashboard
description: Use when the user runs /dashboard [topic] or asks to open, create or refresh the project tracking dashboard - a private claude.ai artifact per project showing the live cycle map, active agents, plans, PRs, CI, tokens per model, GPT/DeepSeek/Grok usage and Claude/GPT debates. Also called by /cycle at each step.
---

# Dashboard: one tracking board per project

Bridge: `python3 <this skill's base directory>/../../bin/dashboard_collect.py`.
Page: `<this skill's base directory>/../../dashboard/dashboard.html`.

## Steps

1. **Project root**: `git rev-parse --show-toplevel` from the current directory. Not a git repo: say the dashboard needs one and stop.
2. **GitHub account** (global CLAUDE.md): `anthonyguillaume_getlink` if the root path contains `/Eurotunnel/`, otherwise `anthonyguillaume`.
3. **Collect** into your scratchpad (never into the project):
   `GH_TOKEN=$(gh auth token -u <account>) python3 .../bin/dashboard_collect.py --root <root> > <scratchpad>/board.json`
   Read the JSON only to check it parsed; never edit a number by hand.
4. **Artifact**: read `<root>/docs/dashboard/config.json`.
   - **Missing**: copy the page to `<scratchpad>/dashboard-<project>.html` and publish it with the Artifact tool: `icon: "chart"`, `description: "Suivi du projet <project>"`, and
     `capabilities: {"db": {"rules": [{"path": "board", "read": "view", "write": "owner"}, {"path": "events", "read": "view", "write": "owner"}]}}`.
     Write `{"artifact": "<url>", "pageVersion": "<ai-team plugin version>"}` to `<root>/docs/dashboard/config.json` and tell the user to commit it (the same link then works from any machine).
   - **Present**: do not republish. Exception: the ai-team plugin version (`.claude-plugin/plugin.json`) is newer than `pageVersion`: republish the page to the same `url` (read it first, omit `capabilities` to keep the stored rules), then update `pageVersion`.
5. **Write the numbers** with `ArtifactData` (load it with ToolSearch if needed), one `batch` on the artifact url:
   - `set board/latest` from `board.json` (`file_path`), with `if_version` = the version returned by a `get` of `board/latest` just before (omit it only when the document does not exist yet);
   - when a topic was given (`/dashboard <topic>`, or the step name when called by /cycle): `set events/<YYYYMMDD-HHMMSS>-<topic-slug>` with `{"at": "<ISO time>", "title": "<topic>", "kind": "step"}`.
6. **First publish only**: one `ArtifactData list` of `board` and of `events` to check the writes landed; say in one line what you checked.
7. **Open** the artifact (Artifact `open`) unless called by /cycle.

## Rules

- Counters only: never put prompts, answers, file contents, secrets or personal data in `board/*` or `events/*`. Event titles are short step names.
- Never republish to change numbers: numbers go through `ArtifactData`.
- Existing dashboards built by a project itself (Orbital, OrbitalInvest, bowtrail have `rules/dashboard.md`): if the project has `rules/dashboard.md`, follow that file instead of this skill.
- No em dashes, middle dots or emoji in what you write.
