#!/usr/bin/env bash
# codex-agent.sh - the single Codex CLI entry point for Agent Orchestra.
#
# Three modes, no plugin layer, no extra abstraction:
#   consult    read-only codex exec (investigation, second opinions, analysis)
#   review     native codex review (defaults to --uncommitted)
#   implement  guarded workspace-write codex exec (bounded delegation)
#
# Purpose: offload token-heavy work to Codex (config-default flagship,
# gpt-5.6-sol under current policy) so Claude usage and rate limits are
# preserved for conductor judgment, verification, and final edits.
#
# SAFETY (do not weaken):
#   * Never uses danger-full-access or --dangerously-bypass-approvals-and-sandbox.
#   * consult/review are read-only. implement requires --allow-write and refuses
#     main/master without an explicit --allow-main.
#   * Prompts egress to OpenAI: never pass secrets; a lightweight regex guard
#     refuses obvious secret material.
#   * Codex output is UNTRUSTED advisory text/diffs. The caller verifies.
#   * Every mode is time-bounded by default so a stalled call cannot hang the
#     conductor. Override with --timeout N (0 disables) or CODEX_AGENT_TIMEOUT.
#   * Usage-limit guard: all modes clamp a max/ultra effort config down to
#     xhigh (user policy — heavy modes devour Plus-subscription limits).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  codex-agent.sh consult [--cd DIR] [--model MODEL] [--effort E] [--with-mcp] [--timeout N] -- "<prompt>"
  codex-agent.sh review  [--cd DIR] [--base REF|--commit SHA|--uncommitted] [--model MODEL] [--effort E] [--timeout N] [--prompt TEXT]
  codex-agent.sh implement --allow-write [--cd DIR] [--model MODEL] [--effort E] [--scope PATH]... [--allow-main] [--timeout N] -- "<task>"

Defaults:
  consult    read-only codex exec, MCP off, effort floored to high, 900s timeout
  review     codex review --uncommitted, 1800s timeout
  implement  workspace-write codex exec guarded by --allow-write, 3600s timeout

Timeout precedence: --timeout > CODEX_AGENT_TIMEOUT > per-mode default. 0 disables.
Model: intentionally not pinned; with no --model, Codex uses ~/.codex/config.toml
(e.g. gpt-5.6-sol), so nothing here goes stale. Override per call with --model.
Effort: --effort low|medium|high|xhigh wins over config; max/ultra are refused
(they devour subscription usage limits) and a max/ultra config is clamped to
xhigh. Default is high (field-tested; medium output quality was not
acceptable); use xhigh per call for the hardest tasks.

The wrapper never uses danger-full-access, never bypasses sandbox/approvals,
and instructs Codex to never commit or push.
EOF
}

die() {
  echo "error: $*" >&2
  exit 2
}

need_value() {
  # need_value <flag> <argc-remaining>
  [ "$2" -ge 2 ] || die "$1 requires a value"
}

secret_re='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|github_pat_|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|password[[:space:]]*[:=]|api[_ -]?key[[:space:]]*[:=]|token[[:space:]]*[:=]'

check_prompt() {
  local prompt="$1"
  [ -n "$prompt" ] || die "prompt/task is required"
  if printf '%s' "$prompt" | grep -qiE "$secret_re"; then
    die "prompt appears to contain a secret; redact before invoking Codex (egress to OpenAI)"
  fi
}

ensure_codex() {
  command -v codex >/dev/null 2>&1 || die "'codex' CLI not found on PATH; install with: npm install -g @openai/codex && codex login"
}

current_branch() {
  git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null || true
}

is_git_repo() {
  git -C "$1" rev-parse --git-dir >/dev/null 2>&1
}

resolve_timeout() {
  # resolve_timeout <flag-value> <mode-default>
  if [ -n "$1" ]; then
    printf '%s' "$1"
  elif [ -n "${CODEX_AGENT_TIMEOUT:-}" ]; then
    printf '%s' "$CODEX_AGENT_TIMEOUT"
  else
    printf '%s' "$2"
  fi
}

# Bounded execution: a stalled Codex call fails fast instead of hanging the
# conductor forever. Uses timeout(1)/gtimeout(1) when present, else a portable
# watchdog (stock macOS has neither).
run_bounded() {
  local seconds="$1"
  shift
  if [ -z "$seconds" ] || [ "$seconds" = "0" ]; then
    exec "$@"
  elif command -v timeout >/dev/null 2>&1; then
    exec timeout "$seconds" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    exec gtimeout "$seconds" "$@"
  else
    "$@" &
    local cmd_pid=$!
    ( sleep "$seconds"; kill -TERM "$cmd_pid" 2>/dev/null ) &
    local watch_pid=$!
    local status=0
    wait "$cmd_pid" || status=$?
    kill "$watch_pid" 2>/dev/null || true
    wait "$watch_pid" 2>/dev/null || true
    [ "$status" -gt 128 ] && echo "error: codex call exceeded ${seconds}s and was terminated" >&2
    exit "$status"
  fi
}

# Effort policy (user: Plus subscription, gpt-5.6-sol lane; field-tested
# 2026-07-10 — Sol medium output quality was unacceptable despite OpenAI
# staff guidance, so the default stands at high; xhigh per call for the
# hardest tasks; max/ultra devour usage limits and stay banned):
#   * per-call --effort accepts low|medium|high|xhigh and wins over config;
#     max/ultra are refused outright;
#   * without --effort, every mode clamps a max/ultra config down to xhigh,
#     and consults floor a low/medium config up to high.
validate_effort() {
  case "$1" in
    low|medium|high|xhigh) : ;;
    max|ultra) die "--effort $1 refused (policy: max/ultra devour Plus usage limits; ceiling is xhigh)" ;;
    *) die "invalid --effort '$1' (use low, medium, high, or xhigh)" ;;
  esac
}

# Prints the override effort, or nothing when the config value stands.
effort_override() {
  # effort_override <mode>
  local cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  local eff
  eff=$(grep -E '^[[:space:]]*model_reasoning_effort' "$cfg" 2>/dev/null | head -1 | sed -E 's/.*=[[:space:]]*"?([A-Za-z]+)"?.*/\1/')
  case "$eff" in
    max|ultra) printf 'xhigh' ;;
    high|xhigh) : ;;
    *) [ "$1" = "consult" ] && printf 'high' ;;
  esac
}

run_consult() {
  local cd_dir="" model="" with_mcp=0 prompt="" timeout_flag="" effort=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cd|-C) need_value "$1" "$#"; cd_dir="$2"; shift 2 ;;
      --model|-m) need_value "$1" "$#"; model="$2"; shift 2 ;;
      --effort) need_value "$1" "$#"; validate_effort "$2"; effort="$2"; shift 2 ;;
      --timeout) need_value "$1" "$#"; timeout_flag="$2"; shift 2 ;;
      --with-mcp) with_mcp=1; shift ;;
      --) shift; prompt="$*"; break ;;
      -h|--help) usage; exit 0 ;;
      -*) die "unknown consult flag: $1" ;;
      *) prompt="${prompt:+$prompt }$1"; shift ;;
    esac
  done
  check_prompt "$prompt"
  ensure_codex
  [ -z "$cd_dir" ] || [ -d "$cd_dir" ] || die "directory not found: $cd_dir"

  local timeout
  timeout="$(resolve_timeout "$timeout_flag" 900)"

  local cmd=(codex exec --sandbox read-only)
  # Advisory consults disable Codex MCP servers by default: a read-only review
  # needs no connectors, and one waiting on auth can hang the whole call.
  [ "$with_mcp" -eq 0 ] && cmd+=(-c 'mcp_servers={}')
  [ -n "$cd_dir" ] && cmd+=(--cd "$cd_dir")
  # codex refuses to run outside a git repo; consults of ad-hoc directories are
  # legitimate, so skip that check when the target is not a repo.
  is_git_repo "${cd_dir:-$PWD}" || cmd+=(--skip-git-repo-check)
  [ -n "$model" ] && cmd+=(-m "$model")
  local eff_ov
  eff_ov="${effort:-$(effort_override consult)}"
  [ -n "$eff_ov" ] && cmd+=(-c "model_reasoning_effort=\"$eff_ov\"")
  cmd+=(-- "$prompt")

  echo "Codex consult: read-only; model=${model:-config-default}; cd=${cd_dir:-$PWD}; timeout=${timeout}s" >&2
  run_bounded "$timeout" "${cmd[@]}"
}

run_review() {
  local cd_dir="" model="" prompt="" target_seen=0 timeout_flag="" effort=""
  local cmd=(codex review)
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --base|--commit|--title)
        need_value "$1" "$#"
        cmd+=("$1" "$2")
        target_seen=1
        shift 2
        ;;
      --uncommitted)
        cmd+=(--uncommitted)
        target_seen=1
        shift
        ;;
      --cd|-C) need_value "$1" "$#"; cd_dir="$2"; shift 2 ;;
      --model|-m) need_value "$1" "$#"; model="$2"; shift 2 ;;
      --effort) need_value "$1" "$#"; validate_effort "$2"; effort="$2"; shift 2 ;;
      --timeout) need_value "$1" "$#"; timeout_flag="$2"; shift 2 ;;
      --prompt) need_value "$1" "$#"; prompt="$2"; shift 2 ;;
      --) shift; prompt="$*"; break ;;
      -h|--help) usage; exit 0 ;;
      -*) die "unknown review flag: $1" ;;
      *) prompt="${prompt:+$prompt }$1"; shift ;;
    esac
  done
  ensure_codex
  if [ -n "$cd_dir" ]; then
    [ -d "$cd_dir" ] || die "directory not found: $cd_dir"
    # codex review has no --cd flag; it reviews the repo at the current directory.
    cd "$cd_dir" || die "cannot cd to: $cd_dir"
  fi
  is_git_repo "$PWD" || die "codex review needs a git repository (cwd: $PWD)"

  local timeout
  timeout="$(resolve_timeout "$timeout_flag" 1800)"

  [ "$target_seen" -eq 1 ] || cmd+=(--uncommitted)
  [ -n "$model" ] && cmd+=(-c "model=\"$model\"")
  local eff_ov
  eff_ov="${effort:-$(effort_override review)}"
  [ -n "$eff_ov" ] && cmd+=(-c "model_reasoning_effort=\"$eff_ov\"")
  if [ -n "$prompt" ]; then
    check_prompt "$prompt"
    cmd+=("$prompt")
  fi

  echo "Codex review: model=${model:-config-default}; dir=$PWD; timeout=${timeout}s" >&2
  run_bounded "$timeout" "${cmd[@]}"
}

run_implement() {
  local cd_dir="$PWD" model="" prompt="" allow_write=0 allow_main=0 timeout_flag="" effort=""
  local scopes=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cd|-C) need_value "$1" "$#"; cd_dir="$2"; shift 2 ;;
      --model|-m) need_value "$1" "$#"; model="$2"; shift 2 ;;
      --effort) need_value "$1" "$#"; validate_effort "$2"; effort="$2"; shift 2 ;;
      --scope) need_value "$1" "$#"; scopes+=("$2"); shift 2 ;;
      --timeout) need_value "$1" "$#"; timeout_flag="$2"; shift 2 ;;
      --allow-write) allow_write=1; shift ;;
      --allow-main) allow_main=1; shift ;;
      --) shift; prompt="$*"; break ;;
      -h|--help) usage; exit 0 ;;
      -*) die "unknown implement flag: $1" ;;
      *) prompt="${prompt:+$prompt }$1"; shift ;;
    esac
  done

  [ "$allow_write" -eq 1 ] || die "implementation requires --allow-write"
  [ -d "$cd_dir" ] || die "directory not found: $cd_dir"
  check_prompt "$prompt"
  ensure_codex
  # workspace-write outside version control has no diff/rollback story; refuse.
  is_git_repo "$cd_dir" || die "refusing workspace-write outside a git repository: $cd_dir"

  local branch
  branch="$(current_branch "$cd_dir")"
  case "$branch" in
    main|master)
      [ "$allow_main" -eq 1 ] || die "refusing workspace-write on branch '$branch'; create/switch to a working branch or pass --allow-main explicitly"
      ;;
  esac

  local timeout
  timeout="$(resolve_timeout "$timeout_flag" 3600)"

  local scope_text="No explicit scope paths were provided. Infer the minimal safe scope from the task."
  if [ "${#scopes[@]}" -gt 0 ]; then
    scope_text="Only modify these paths unless the task is impossible without expanding scope:"
    local scope
    for scope in "${scopes[@]}"; do
      [ -n "$scope" ] || die "--scope requires a non-empty path"
      scope_text="$scope_text
- $scope"
    done
  fi

  local guarded_prompt
  guarded_prompt="You are Codex running as a bounded implementation agent.

Task:
$prompt

Scope:
$scope_text

Rules:
- Make the smallest correct patch.
- Do not commit, push, create PRs, or alter remotes.
- Do not delete user data or broad directories.
- Do not read or modify secret-bearing files such as .env, private keys, tokens, or credential stores.
- Run focused validation if safe and available.
- Finish with a concise summary of changed files, tests run, and any residual risks."

  local cmd=(codex exec --sandbox workspace-write -c 'mcp_servers={}' --cd "$cd_dir")
  [ -n "$model" ] && cmd+=(-m "$model")
  local eff_ov
  eff_ov="${effort:-$(effort_override implement)}"
  [ -n "$eff_ov" ] && cmd+=(-c "model_reasoning_effort=\"$eff_ov\"")
  cmd+=(-- "$guarded_prompt")

  echo "Codex implementation: workspace-write; model=${model:-config-default}; cd=$cd_dir; branch=${branch:-unknown}; timeout=${timeout}s" >&2
  run_bounded "$timeout" "${cmd[@]}"
}

main() {
  local mode="${1:-}"
  case "$mode" in
    consult) shift; run_consult "$@" ;;
    review) shift; run_review "$@" ;;
    implement) shift; run_implement "$@" ;;
    -h|--help|"") usage ;;
    *) die "unknown mode: $mode" ;;
  esac
}

main "$@"
