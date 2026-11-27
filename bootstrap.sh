#!/usr/bin/env bash
# Rebuild the ai-team setup on a machine.
#   ./bootstrap.sh --check   report OK / MISSING for each piece, install nothing (exit 1 if something is missing)
#   ./bootstrap.sh           same checks, then offer to fix each MISSING piece, asking [y/N] every time
# Keys and logins never travel: codex login, XAI_API_KEY, ~/.deepseek-mcp/config.json are redone per machine.
set -u

REPO="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-install}"
MISSING=0
IMPORT_LINE="@$REPO/rules/team.md"

ok()   { echo "OK $1"; }
miss() { echo "MISSING $1"; MISSING=1; }
have() { command -v "$1" >/dev/null 2>&1; }

ask() { # ask "question" "command"
  [ "$MODE" = "--check" ] && return 0
  printf '%s\n  -> %s\n  Run it? [y/N] ' "$1" "$2"
  read -r answer </dev/tty || answer=n
  [ "$answer" = "y" ] && bash -c "$2"
}

check_tool() { # check_tool name install-command
  if have "$1"; then ok "$1"; else miss "$1"; ask "Install $1" "$2"; fi
}

check_tool claude "curl -fsSL https://claude.ai/install.sh | bash"
check_tool codex "brew install codex"

if have codex; then
  if codex login status 2>/dev/null | grep -qi "logged in" && ! codex login status 2>/dev/null | grep -qi "not logged"; then
    ok "codex login"
  else
    miss "codex login"; ask "Log in to Codex with the ChatGPT account" "codex login"
  fi
fi

if have claude; then
  installed="$(claude plugin list 2>/dev/null)"
  markets="$(claude plugin marketplace list 2>/dev/null)"
  while read -r kind name repo; do
    case "$kind" in
      marketplace)
        if grep -q "$name" <<<"$markets"; then ok "marketplace $name"
        else miss "marketplace $name"; ask "Add marketplace $name" "claude plugin marketplace add $repo"; fi ;;
      plugin)
        if grep -q "${name%@*}@" <<<"$installed"; then ok "plugin $name"
        else miss "plugin $name"; ask "Install plugin $name" "claude plugin install $name"; fi ;;
    esac
  done < <(grep -v '^#' "$REPO/manifest/plugins.txt")

  if grep -q "ai-team@" <<<"$installed"; then ok "plugin ai-team"
  else miss "plugin ai-team"
    ask "Install ai-team from this folder" "claude plugin marketplace add '$REPO' && claude plugin install ai-team@ai-team"; fi

  if claude mcp list 2>/dev/null | grep -q "^deepseek"; then ok "mcp deepseek"
  else miss "mcp deepseek"
    ask "Install the DeepSeek MCP server (then put your key in ~/.deepseek-mcp/config.json)" \
      "mkdir -p '$HOME/Dev/mcp' && git clone https://github.com/PsChina/deepseek-as-subagent '$HOME/Dev/mcp/deepseek-as-subagent' && cd '$HOME/Dev/mcp/deepseek-as-subagent' && ./install.sh"
  fi
fi

if [ -n "${XAI_API_KEY:-}" ]; then ok "XAI_API_KEY"
else miss "XAI_API_KEY"; [ "$MODE" = "--check" ] || echo "  -> add 'export XAI_API_KEY=...' to ~/.zshrc yourself (never paste it in a chat)"; fi

if [ -n "${COMFYUI_URL:-}" ]; then ok "COMFYUI_URL"
else echo "INFO COMFYUI_URL not set, default http://192.168.0.96:8188"; fi

if grep -qF "$IMPORT_LINE" "$HOME/.claude/CLAUDE.md" 2>/dev/null; then ok "CLAUDE.md imports team rules"
else miss "CLAUDE.md imports team rules"
  ask "Add the team rules import to ~/.claude/CLAUDE.md" "mkdir -p '$HOME/.claude' && printf '\n# ai-team\n%s\n' '$IMPORT_LINE' >> '$HOME/.claude/CLAUDE.md'"; fi

while read -r skill source; do
  [ "$source" = "unknown" ] && echo "INFO skill $skill: source unknown, copy it by hand from the old machine"
done < <(grep -v '^#' "$REPO/manifest/third-party-skills.txt")

exit "$MISSING"
