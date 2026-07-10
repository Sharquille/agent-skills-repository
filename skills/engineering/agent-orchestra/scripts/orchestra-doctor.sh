#!/usr/bin/env bash
# Read-only readiness check for Agent Orchestra integrations.
# Checks the two direct integration paths (Codex CLI, OpenCode CLI), their
# auth, the canonical wrappers, and the standard delegation lanes.
# Pass --models to list the models reachable for steering instead: the Codex
# config default (override per call with codex-agent.sh --model M) and the
# full OpenCode catalog (usable via consult-opencode.sh --model provider/model).

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# --models: model discovery for conductor steering (read-only, then exit).
if [ "${1:-}" = "--models" ]; then
  codex_cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  printf 'Codex (steer per call: codex-agent.sh <mode> --model M):\n'
  if have codex; then
    if [ -f "$codex_cfg" ]; then
      model_lines="$(grep -E '^[[:space:]]*model(_reasoning_effort)?[[:space:]]*=' "$codex_cfg" 2>/dev/null | sed 's/^[[:space:]]*/  /')"
      if [ -n "$model_lines" ]; then
        printf '%s\n' "$model_lines"
      else
        printf '  (no model pinned in config.toml; Codex uses its built-in default)\n'
      fi
    else
      printf '  (no config.toml at %s)\n' "$codex_cfg"
    fi
  else
    printf '  codex CLI not on PATH\n'
  fi
  printf '\nOpenCode catalog (steer via --model provider/model; lane defaults via ORCHESTRA_LANE_*):\n'
  if have opencode; then
    opencode models 2>/dev/null || printf '  (could not list models; run: opencode auth login)\n'
  else
    printf '  opencode CLI not on PATH\n'
  fi
  printf '\nOnboard unfamiliar models before routing work to them (references/model-routing.md).\n'
  exit 0
fi

printf 'Agent Orchestra readiness check\n'
printf 'Skill: %s\n\n' "$SKILL_DIR"

# --- Codex CLI (flagship lane) ---
if have codex; then
  codex_version="$(version_of codex --version)"
  ok "codex CLI available: ${codex_version:-unknown version}"
  login_line="$(codex login status 2>&1 | head -n 1)"
  if codex login status >/dev/null 2>&1; then
    ok "codex auth: ${login_line:-logged in}"
  else
    warn "codex auth: not logged in (run: codex login)"
  fi
  codex_cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  codex_model="$(grep -E '^[[:space:]]*model[[:space:]]*=' "$codex_cfg" 2>/dev/null | head -1 | sed -E 's/.*=[[:space:]]*"([^"]*)".*/\1/')"
  codex_effort="$(grep -E '^[[:space:]]*model_reasoning_effort' "$codex_cfg" 2>/dev/null | head -1 | sed -E 's/.*=[[:space:]]*"?([A-Za-z]+)"?.*/\1/')"
  info "codex defaults: model=${codex_model:-unset}; reasoning=${codex_effort:-unset}"
else
  warn "codex CLI is not on PATH. Install with: npm install -g @openai/codex && codex login"
fi

echo

# --- OpenCode CLI (Kimi / MiniMax / DeepSeek / MiMo lanes) ---
lane_code="${ORCHESTRA_LANE_CODE:-openrouter/moonshotai/kimi-k2.7-code}"
lane_prose="${ORCHESTRA_LANE_PROSE:-openrouter/xiaomi/mimo-v2.5-pro}"
lane_reasoning="${ORCHESTRA_LANE_REASONING:-openrouter/minimax/minimax-m3}"
lane_context="${ORCHESTRA_LANE_CONTEXT:-openrouter/deepseek/deepseek-v4-flash}"

if have opencode; then
  opencode_version="$(version_of opencode --version)"
  ok "opencode CLI available: ${opencode_version:-unknown version}"
  models_list="$(opencode models 2>/dev/null)"
  if [ -n "$models_list" ]; then
    for lane in "code:$lane_code" "reasoning:$lane_reasoning" "context:$lane_context" "prose:$lane_prose"; do
      lane_name="${lane%%:*}"
      lane_model="${lane#*:}"
      if printf '%s\n' "$models_list" | grep -qxF "$lane_model"; then
        ok "lane '$lane_name' model available: $lane_model"
      else
        warn "lane '$lane_name' model NOT in 'opencode models' catalog: $lane_model"
      fi
    done
  else
    warn "could not list OpenCode models; provider auth may be missing (run: opencode auth login)"
  fi
else
  warn "opencode CLI is not on PATH; OpenCode lanes (Kimi/MiniMax/DeepSeek/MiMo) will be skipped."
fi

echo

# --- Canonical wrappers ---
codex_agent="$SKILL_DIR/scripts/codex-agent.sh"
opencode_wrapper="$SKILL_DIR/scripts/consult-opencode.sh"
opencode_impl="$SKILL_DIR/scripts/opencode-implement.sh"
codex_shim="$SKILL_DIR/scripts/consult-codex.sh"

[ -x "$codex_agent" ] && ok "Codex entry point executable: $codex_agent" || warn "Codex entry point missing or not executable: $codex_agent"
[ -x "$opencode_wrapper" ] && ok "OpenCode consult wrapper executable: $opencode_wrapper" || warn "OpenCode consult wrapper missing or not executable: $opencode_wrapper"
[ -x "$opencode_impl" ] && ok "OpenCode implement wrapper executable: $opencode_impl" || warn "OpenCode implement wrapper missing or not executable: $opencode_impl"
[ -x "$codex_shim" ] && ok "legacy consult-codex shim executable: $codex_shim" || warn "legacy consult-codex shim missing or not executable: $codex_shim"

echo
if [ "$status" -eq 0 ]; then
  info "All lanes ready. Delegate heavy work off-Claude:"
else
  info "Some lanes degraded (see WARN above). Working lanes:"
fi
cat <<EOF
  codex-agent.sh consult|review|implement          -> Codex config-default flagship (primary)
  consult-opencode.sh --lane code      --sealed    -> $lane_code
  consult-opencode.sh --lane reasoning --sealed    -> $lane_reasoning (high reasoning)
  consult-opencode.sh --lane context   --sealed    -> $lane_context (cheap, ~1M ctx)
  consult-opencode.sh --lane prose     --sealed    -> $lane_prose
  opencode-implement.sh --allow-write (Codex fallback; edits only, no shell)
EOF

exit "$status"
