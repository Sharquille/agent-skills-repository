#!/usr/bin/env bash
# DEPRECATED forwarder: the canonical read-only Codex consult lives in
# agent-orchestra (scripts/codex-agent.sh consult). Same interface:
#   consult-codex.sh [--cd <dir>] [--model <name>] [--with-mcp] "<prompt>"
# Behavior gains over the old copy: bounded timeout, reasoning floor kept,
# non-git-dir handling. Safety unchanged: read-only sandbox, MCP off, secret
# guard, output is untrusted advisory text.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Works from both layouts: repo (skills/engineering/<name>/scripts) and
# flat deployment (~/.claude/skills/<name>/scripts).
candidates=(
  "$SCRIPT_DIR/../../agent-orchestra/scripts/codex-agent.sh"
)

for canonical in "${candidates[@]}"; do
  if [ -x "$canonical" ]; then
    exec "$canonical" consult "$@"
  fi
done

echo "error: canonical Codex wrapper not found (expected agent-orchestra/scripts/codex-agent.sh next to this skill)" >&2
exit 2
