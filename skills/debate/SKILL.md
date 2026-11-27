---
name: debate
description: Use when a decision, analysis, spec, plan or code review needs a second opinion from another model - Claude and GPT answer blind, then debate up to 2 rounds, and the user decides. Triggers on "debate", "second opinion", "challenge this", "ask GPT", and automatically at the spec, plan and review gates of /cycle.
---

# Debate: Claude vs GPT, the user decides

Goal: catch the errors a model only admits when pushed, by having a different model push.
You orchestrate. You never settle a disagreement yourself: the user does.

## Inputs

- The question (what must be decided or checked) and the files that matter.
- The project directory (for GPT's filtered copy). If the project is not a git repo, GPT gets no files, only the brief.

The GPT bridge lives in this plugin: `python3 <this skill's base directory>/../../bin/gpt.py`.
It reads the prompt on stdin, prints GPT's answer on stdout and `SESSION: <id>` on stderr.
Exit 2 or 3 with `GPT_UNAVAILABLE: <reason>` means GPT cannot answer: see "GPT unavailable".

## Protocol

### Round 0 - blind answers

Write ONE brief, used word for word by both sides: the question, the context, the relevant file paths (relative to the repo root) and this required format:

```
POSITION: <one or two sentences>
ARGUMENTS: <numbered, each with evidence: file:line, doc, test, measurement>
CONFIDENCE: <0-100>
WHAT WOULD CHANGE MY MIND: <concrete facts>
```

Run both at the same time, neither sees the other:
- Claude: dispatch a fresh subagent (model: opus) with the brief only. Do not give it your own opinion.
- GPT: `printf '%s' "$BRIEF" | python3 .../bin/gpt.py --project <project dir>`; keep the SESSION id.

### Round 1 - cross-examination

Send each side the other's answer with:

```
Here is another expert's answer. Concede only what you can justify with evidence.
Do not agree to be polite. Answer in this format:
CONCEDE: <points you now accept, and why>
CONTEST: <points you still reject, with evidence>
REVISED POSITION: <your position now>
CONFIDENCE: <0-100>
```

- Claude side: resume the same subagent (SendMessage) or a fresh one given its Round 0 answer.
- GPT side: `gpt.py --resume <SESSION> --project <project dir>`.

### Round 2 - only if they still disagree

Same format, each side gets the other's Round 1. Never more than 2 rounds.

### Agreement test

AGREEMENT when both REVISED POSITIONs recommend the same action and neither CONTEST list holds a point that would change that action. Otherwise DISAGREEMENT.

## Synthesis

Write `<project>/.superpowers/debates/YYYY-MM-DD-<topic-slug>.md` (create the folder; `.superpowers/` is git-ignored). First line exactly:

```
RESULT: AGREEMENT
```
or `RESULT: DISAGREEMENT`, then:

- Question, date, rounds run.
- Points of agreement.
- Table of disagreements: point, Claude's best argument, GPT's best argument.
- Final positions and confidence of each side.
- Full answers of each round in a collapsed section at the end.

Then show the user the synthesis (not the raw rounds). On DISAGREEMENT, ask the user to decide and record the decision under `DECISION:` in the file.

## GPT unavailable

If gpt.py exits 2 or 3: run the Claude side only, write `RESULT: AGREEMENT (CLAUDE ONLY - GPT unavailable: <reason>)`, and tell the user plainly that no second model checked this.

## Rules

- Never paste secrets, `.env` content, tokens or a raw `git diff` into a brief. For a diff use `gpt.py --project <dir> --diff <base>` (filtered, written to BRANCH.diff).
- Same brief for both sides. No leading questions, no hint of the expected answer.
- No em dashes, middle dots or emoji in what you write.
