#!/usr/bin/env bash
# DEPRECATED forwarder: the canonical read-only OpenCode consult wrapper lives
# in agent-orchestra (scripts/consult-opencode.sh). Same interface plus new
# --lane code|reasoning|context|prose shortcuts. Safety unchanged: explicit
# model, deny-all inline agent, sealed mode, timeouts, secret guard.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Works from both layouts: repo (skills/engineering/<name>/scripts) and
# flat deployment (~/.claude/skills/<name>/scripts).
candidates=(
  "$SCRIPT_DIR/../../agent-orchestra/scripts/consult-opencode.sh"
)

for canonical in "${candidates[@]}"; do
  if [ -x "$canonical" ]; then
    exec "$canonical" "$@"
  fi
done

echo "error: canonical OpenCode wrapper not found (expected agent-orchestra/scripts/consult-opencode.sh next to this skill)" >&2
exit 2
