#!/usr/bin/env bash
# Passive prerequisite check for Agent Orchestra integrations. It makes no
# model call and writes no project file; invoked CLIs may update their own logs
# or caches while reporting local state.
#
# States are deliberately distinct:
#   installed      the CLI/wrapper exists locally;
#   authenticated  the CLI's local auth check succeeds, when one exists;
#   model-listed   the configured OpenCode route appears in its catalog;
#   callable       always unverified here because doctor never makes a paid or
#                  model-consuming invocation.
#
# Default mode is descriptive and exits zero after printing degraded states.
# Pass --require-ready for automation: it exits nonzero unless the local CLI,
# auth/catalog, configured lane, and wrapper checks all pass. This still does
# not claim that a live provider invocation succeeded.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

status=0
require_ready=0
show_models=0

usage() {
  cat <<'EOF'
Usage: orchestra-doctor.sh [--models] [--require-ready]

  (no flags)       descriptive readiness report; degraded states still exit 0
  --models         list configured Codex defaults and the OpenCode catalog
  --require-ready  exit 1 unless every local readiness check passes

Neither mode makes a model call. "callable" therefore remains unverified.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --models) show_models=1 ;;
    --require-ready) require_ready=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

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

state_line() {
  printf '[STATE] %s\n' "$*"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

version_of() {
  local output
  output="$("$@" 2>/dev/null)" || return 1
  [ -n "$output" ] || return 1
  printf '%s\n' "$output" | head -n 1
}

finish() {
  if [ "$require_ready" -eq 1 ]; then
    exit "$status"
  fi
  exit 0
}

codex_cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
lane_code="${ORCHESTRA_LANE_CODE:-opencode-go/kimi-k3}"
lane_prose="${ORCHESTRA_LANE_PROSE:-openrouter/xiaomi/mimo-v2.5-pro}"
lane_reasoning="${ORCHESTRA_LANE_REASONING:-opencode-go/kimi-k3}"
lane_context="${ORCHESTRA_LANE_CONTEXT:-opencode-go/deepseek-v4-flash}"

if [ "$show_models" -eq 1 ]; then
  printf 'Codex configuration (steer per call: orchestra-agent.sh <mode> --model M):\n'
  if have codex; then
    if [ -f "$codex_cfg" ]; then
      model_lines="$(grep -E '^[[:space:]]*model(_reasoning_effort)?[[:space:]]*=' "$codex_cfg" 2>/dev/null | sed 's/^[[:space:]]*/  /')"
      if [ -n "$model_lines" ]; then
        printf '%s\n' "$model_lines"
      else
        printf '  (no model pinned; Codex uses its built-in default)\n'
      fi
    else
      printf '  (no config.toml at %s)\n' "$codex_cfg"
    fi
  else
    warn "codex CLI not installed"
  fi

  printf '\nOpenCode catalog (configured routes are useful only when listed):\n'
  if have opencode; then
    if models_list="$(opencode --pure models 2>/dev/null)" && [ -n "$models_list" ]; then
      printf '%s\n' "$models_list"
    else
      warn "OpenCode model catalog unavailable; authentication or provider access may be missing"
    fi
  else
    warn "opencode CLI not installed"
  fi
  printf '\n[STATE] callable=unverified (doctor makes no model call)\n'
  printf 'Onboard unfamiliar models before routing work to them (references/model-routing.md).\n'
  if [ "$require_ready" -eq 0 ]; then
    finish
  fi
  printf '\n[INFO] --require-ready also checks auth inventory, configured routes, and wrappers.\n\n'
fi

printf 'Agent Orchestra readiness check\n'
printf 'Skill: %s\n\n' "$SKILL_DIR"

# --- Codex CLI (flagship lane) ---
codex_installed=no
codex_authenticated=no
codex_model=unset
codex_effort=unset
if have codex; then
  if codex_version="$(version_of codex --version)"; then
    codex_installed=yes
    ok "codex CLI installed: $codex_version"
  else
    warn "codex command exists but --version failed"
  fi
  if [ "$codex_installed" = yes ] && codex login status >/dev/null 2>&1; then
    codex_authenticated=reported
    ok "codex authentication reported by the CLI"
  else
    warn "codex authentication was not reported; inspect with: codex login status"
  fi
  codex_model="$(grep -E '^[[:space:]]*model[[:space:]]*=' "$codex_cfg" 2>/dev/null | head -1 | sed -E "s/^[^=]*=[[:space:]]*['\"]?([^'\"[:space:]#]+).*/\1/")"
  codex_effort="$(grep -E '^[[:space:]]*model_reasoning_effort' "$codex_cfg" 2>/dev/null | head -1 | sed -E "s/^[^=]*=[[:space:]]*['\"]?([^'\"[:space:]#]+).*/\1/")"
  codex_model="${codex_model:-unset}"
  codex_effort="${codex_effort:-unset}"
else
  warn "codex CLI is not installed (install @openai/codex, then authenticate)"
fi
state_line "codex installed=$codex_installed authenticated=$codex_authenticated configured-model=$codex_model model-listed=unknown reasoning=$codex_effort invocation=unverified"

echo

# --- OpenCode CLI (Kimi / DeepSeek / MiMo lanes) ---
opencode_installed=no
opencode_credentials=unknown
opencode_catalog=unavailable
models_list=""
if have opencode; then
  if opencode_version="$(version_of opencode --version)"; then
    opencode_installed=yes
    ok "opencode CLI installed: $opencode_version"
  else
    warn "opencode command exists but --version failed"
  fi
  auth_inventory=""
  if [ "$opencode_installed" = yes ] && auth_inventory="$(opencode --pure auth list 2>/dev/null)"; then
    if [ -n "$auth_inventory" ]; then
      if printf '%s\n' "$auth_inventory" | grep -qi 'openrouter'; then
        opencode_credentials=openrouter-reported
      else
        opencode_credentials=other-reported
      fi
      ok "OpenCode credential inventory reported local provider configuration"
    else
      opencode_credentials=none-reported
      warn "OpenCode credential inventory reported no configured provider"
    fi
  else
    warn "OpenCode credential inventory unavailable; provider authentication is unknown"
  fi
  if [ "$opencode_installed" = yes ] && models_list="$(opencode --pure models 2>/dev/null)" && [ -n "$models_list" ]; then
    opencode_catalog=available
    ok "OpenCode model catalog available"
  else
    warn "OpenCode model catalog unavailable; authentication or provider access may be missing"
  fi
else
  warn "opencode CLI is not installed; OpenCode lanes will be skipped"
fi
state_line "opencode installed=$opencode_installed credentials=$opencode_credentials catalog=$opencode_catalog invocation=unverified"

printf '\nConfigured OpenCode routes:\n'
for lane in "code:$lane_code" "reasoning:$lane_reasoning" "context:$lane_context" "prose:$lane_prose"; do
  lane_name="${lane%%:*}"
  lane_model="${lane#*:}"
  lane_state=unverified
  case "$lane_model" in
    */*) : ;;
    *)
      lane_state=invalid-route
      warn "lane '$lane_name' must use provider/model form: $lane_model"
      printf '  %-10s %-14s %s\n' "$lane_name" "$lane_state" "$lane_model"
      continue
      ;;
  esac
  if [ "$opencode_catalog" = available ]; then
    if printf '%s\n' "$models_list" | grep -qxF "$lane_model"; then
      lane_state=model-listed
    else
      lane_state=not-listed
      warn "lane '$lane_name' model is not in the OpenCode catalog: $lane_model"
    fi
  fi
  printf '  %-10s %-14s %s\n' "$lane_name" "$lane_state" "$lane_model"
done

echo

# --- Canonical wrappers ---
codex_agent="$SKILL_DIR/scripts/codex-agent.sh"
orchestra_agent="$SKILL_DIR/scripts/orchestra-agent.sh"
opencode_wrapper="$SKILL_DIR/scripts/consult-opencode.sh"
opencode_impl="$SKILL_DIR/scripts/opencode-implement.sh"
codex_shim="$SKILL_DIR/scripts/consult-codex.sh"
scope_lib="$SKILL_DIR/scripts/write-scope.sh"

[ -x "$codex_agent" ] && ok "Codex entry point installed: $codex_agent" || warn "Codex entry point missing or not executable: $codex_agent"
[ -x "$orchestra_agent" ] && ok "Unified selector installed: $orchestra_agent" || warn "Unified selector missing or not executable: $orchestra_agent"
[ -x "$opencode_wrapper" ] && ok "OpenCode consult wrapper installed: $opencode_wrapper" || warn "OpenCode consult wrapper missing or not executable: $opencode_wrapper"
[ -x "$opencode_impl" ] && ok "OpenCode implement wrapper installed: $opencode_impl" || warn "OpenCode implement wrapper missing or not executable: $opencode_impl"
[ -x "$codex_shim" ] && ok "legacy consult-codex shim installed: $codex_shim" || warn "legacy consult-codex shim missing or not executable: $codex_shim"
[ -r "$scope_lib" ] && ok "write-scope library installed: $scope_lib" || warn "write-scope library missing or unreadable: $scope_lib"

echo
if [ "$status" -eq 0 ]; then
  info "Local readiness checks passed. Live callability remains unverified until a bounded invocation succeeds."
else
  info "One or more local readiness checks are degraded. No degraded lane is being reported as working."
fi

finish
