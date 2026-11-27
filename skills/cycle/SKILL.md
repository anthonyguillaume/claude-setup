---
name: cycle
description: Use when the user runs /cycle <idea> or asks for the full multi-agent workflow on a feature or app - brainstorm with the user, then spec, plan, tests, code and review run on their own, with Claude/GPT debates at the spec, plan and review gates. Stops only on a Claude/GPT disagreement and before any push.
---

# Cycle: the multi-model work cycle

Builds on superpowers instead of replacing it. What this skill adds: `/debate` at three gates, the ai-team agents, DeepSeek routing, and a journal of every decision taken without the user.

Read `rules/team.md` of the ai-team plugin (loaded from `~/.claude/CLAUDE.md`) before starting.

## Before starting

- If the session model is not Fable, say so in one line and suggest `/model fable`. Do not block.
- Check the GPT bridge: `codex login status`. Not logged in: say the cycle will run with Claude only until the user runs `! codex login`.
- Phase file: at every phase change write `<project>/.superpowers/cycle.json` as `{"phase": "<phase>", "task": "<short label, e.g. Task 3>", "updatedAt": "<ISO time>"}` with phase one of `idea`, `spec`, `plan`, `tests`, `build`, `review`, `merge`, `push`. The dashboard reads it.
- Dashboard: after writing `cycle.json`, at the end of each task, at each gate (spec, plan, review) and at the end of the cycle, run `/dashboard <step>` (skill `dashboard`, without opening it). If `docs/dashboard/config.json` does not exist yet, skip silently: the user creates the board with a first `/dashboard`.
- Journal: `<project>/.superpowers/progress.md` (git-ignored). One line per automatic decision: `Décision : ... - coût si faux : ...`. Note every `GPT unavailable`.

## Steps

1. **Idea and spec, with the user.** Run `superpowers:brainstorming` with the user (agent `product-owner` for the hypothesis and scope). When the spec is written, run `/debate` on it ("Is this spec complete, consistent and buildable? What is missing or wrong?"). Show the user the synthesis together with the spec. The user approves the spec: this is the only planned stop besides disagreements and push.

2. **Plan, on its own.** Run `superpowers:writing-plans`. Then `/debate` on the plan against the spec.
   - `RESULT: AGREEMENT`: apply the agreed fixes, journal it, choose subagent-driven execution without asking.
   - `RESULT: DISAGREEMENT`: stop, show the synthesis, the user decides.

3. **Build, on its own.** Run `superpowers:subagent-driven-development`.
   - Agents: the project's own `.claude/agents/` when they exist, otherwise ai-team's: `test-writer` first, then `front-react`, `back-csharp`, `back-node` or `back-rust` by stack.
   - Mechanical low-context work goes to DeepSeek (`delegate-to-deepseek`, rules/team.md section 4).
   - Per-task review stays Claude's (`reviewer`), as superpowers does it.
   - Bugs: `superpowers:systematic-debugging`.

4. **Branch review gate.** On the full branch diff, in parallel:
   - agent `reviewer` (Claude, Opus);
   - GPT through agent `challenger` with the same instructions and the same `VERDICT:` format, run as `gpt.py --project <repo> --diff <base>`: the filtered diff (no secrets, `.aiignore` respected) is written to `BRANCH.diff` in GPT's copy and the brief tells GPT to read it. Never paste the raw `git diff` into a brief;
   - agent `security` if the diff touches auth, authorization, data isolation, crypto, secrets, file or URL input, CI workflows or LLM features;
   - agent `qa` if the diff touches UI.

   Compare verdicts:
   - Same verdict: continue (APPROVE) or fix and review again (REQUEST_CHANGES). Two consecutive agreed REQUEST_CHANGES on the same points: stop, the user decides.
   - Different verdicts: `/debate` on the disputed points (2 rounds max). Still different: stop, the user decides.
   - GPT unavailable: continue with Claude's verdict and journal it.

5. **Finish.** `superpowers:verification-before-completion`, then `superpowers:finishing-a-development-branch` up to a local merge. **Always stop before `git push`** and ask the user.

## Rules

- Stop only for: a Claude/GPT disagreement, two agreed REQUEST_CHANGES in a row, an install, a destructive action, and before push.
- Global CLAUDE.md rules first: no push without consent, no Claude mention or `Co-Authored-By` in commits and PRs, right GitHub account, approval before changes outside the launch folder.
- No em dashes, middle dots or emoji in anything written.
