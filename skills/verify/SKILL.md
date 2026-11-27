---
name: verify
description: Use when the user runs /verify to have GPT cross-check Claude's last answer or output in one round - factual errors, invented APIs, files or options, wrong reasoning. Manual only.
disable-model-invocation: true
---

# Verify: GPT cross-checks Claude in one round

The user suspects Claude's last answer may be wrong. Have a different model check it, then answer each point honestly.

The GPT bridge lives in this plugin: `python3 <this skill's base directory>/../../bin/gpt.py`.

## Steps

1. Identify what to check: Claude's last answer or output (or what the user names after `/verify`). Collect the context GPT needs: the user's question, the relevant file paths. Pass `--project <dir>` when the answer is about a git project, so GPT can read the filtered copy.
2. Send GPT this prompt with the material:

```
Check the following answer for errors. Look for: factual errors, APIs, functions,
options, files or commands that do not exist, wrong versions, broken reasoning,
missing cases that change the conclusion. Check against the code when files are
available. For each problem give: the claim, why it is wrong, evidence, the fix.
If you find nothing wrong, say "NO ISSUES" and what you checked.
```

3. For each point GPT raises, check it yourself (read the file, run the command, read the doc). Then answer point by point:
   - `ACCEPTED`: GPT is right, give the corrected answer.
   - `REJECTED`: GPT is wrong, give the evidence.
4. Show the user: the points, your verdict on each, and the corrected answer if anything changed.
5. If a point stays disputed (you reject it and cannot prove it either way), propose `/debate` on that point.

If gpt.py exits 2 or 3 (`GPT_UNAVAILABLE`), tell the user GPT could not check and why. Do not pretend a verification happened.

No em dashes, middle dots or emoji in what you write.
