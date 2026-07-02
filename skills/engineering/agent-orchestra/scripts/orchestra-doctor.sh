#!/usr/bin/env bash
# Read-only readiness check for Agent Orchestra integrations.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ENGINEERING_DIR="$(cd "$SKILL_DIR/.." && pwd)"

status=0

ok() {
  printf '[OK] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
  status=1
}

info() {
  printf '[INFO] %s\n' "$*"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

version_of() {
  "$@" 2>/dev/null | head -n 1
}

printf 'Agent Orchestra readiness check\n'
printf 'Skill: %s\n\n' "$SKILL_DIR"

if have node; then
  node_version="$(version_of node --version)"
  info "node available for optional codex-plugin-cc: ${node_version:-unknown version}"
else
  info "node is not on PATH; only the optional codex-plugin-cc path needs Node.js 18.18 or later."
fi

if have codex; then
  codex_version="$(version_of codex --version)"
  ok "codex CLI available: ${codex_version:-unknown version}"
else
  warn "codex CLI is not on PATH. Install with: npm install -g @openai/codex"
fi

if have opencode; then
  opencode_version="$(version_of opencode --version)"
  ok "opencode CLI available: ${opencode_version:-unknown version}"
else
  warn "opencode CLI is not on PATH; OpenCode lanes will be skipped."
fi

codex_wrapper="$SKILL_DIR/scripts/consult-codex.sh"
codex_agent="$SKILL_DIR/scripts/codex-agent.sh"
opencode_wrapper="$SKILL_DIR/scripts/consult-opencode.sh"
legacy_codex="$REPO_ENGINEERING_DIR/codex-consult/scripts/consult-codex.sh"
legacy_opencode="$REPO_ENGINEERING_DIR/opencode-consult/scripts/consult-opencode.sh"

[ -x "$codex_wrapper" ] && ok "canonical Codex wrapper executable: $codex_wrapper" || warn "canonical Codex wrapper missing or not executable: $codex_wrapper"
[ -x "$codex_agent" ] && ok "Codex agent caller executable: $codex_agent" || warn "Codex agent caller missing or not executable: $codex_agent"
[ -x "$opencode_wrapper" ] && ok "canonical OpenCode wrapper executable: $opencode_wrapper" || warn "canonical OpenCode wrapper missing or not executable: $opencode_wrapper"
[ -x "$legacy_codex" ] && ok "legacy Codex wrapper available: $legacy_codex" || warn "legacy Codex wrapper missing or not executable: $legacy_codex"
[ -x "$legacy_opencode" ] && ok "legacy OpenCode wrapper available: $legacy_opencode" || warn "legacy OpenCode wrapper missing or not executable: $legacy_opencode"

cat <<'EOF'

Claude Code plugin setup is optional. If you still want it, run inside Claude Code:
  /plugin marketplace add openai/codex-plugin-cc
  /plugin install codex@openai-codex
  /reload-plugins
  /codex:setup
EOF

exit "$status"
