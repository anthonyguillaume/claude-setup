---
name: grok
description: Send a prompt to Grok (xAI) when the user explicitly runs /grok - dark or violent fiction, satire, crude humour, visuals other models refuse out of over-caution, X trends. Manual only, never an automatic fallback.
disable-model-invocation: true
---

# Grok

Bridge: `python3 <this skill's base directory>/../../bin/grok.py` reads the prompt on stdin and prints Grok's answer. Needs `XAI_API_KEY` in the environment.

## Steps

1. Take the text the user wrote after `/grok`. Send that text, and only that text, to Grok: no project files, no secrets, no conversation history unless the user asks for it.
2. Show the answer as-is, under a line saying it comes from Grok.
3. On exit 2 or 3 (`GROK_UNAVAILABLE: <reason>`), tell the user the reason. If the key is missing, remind them to add it to `~/.zshrc` themselves, never in the chat.

## Rules

- Only when the user calls /grok. Never route a request to Grok because Claude or GPT refused it: some refusals are well-founded, and this skill is not a way around them.
- Grok's answer is Grok's: do not present it as Claude's, do not edit it silently.
- No em dashes, middle dots or emoji in what you write.
