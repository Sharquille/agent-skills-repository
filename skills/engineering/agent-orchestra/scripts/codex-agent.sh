#!/usr/bin/env bash
# codex-agent.sh - the single Codex CLI entry point for Agent Orchestra.
#
# Three modes, no plugin layer, no extra abstraction:
#   consult    read-only codex exec (investigation, second opinions, analysis)
#   review     native codex review (defaults to --uncommitted)
#   implement  guarded workspace-write codex exec (bounded delegation)
#
# Purpose: offload token-heavy analysis and review to Codex. In the default
# orchestra pipeline Luna/max critiques and Sol/xhigh performs final overview;
# OpenCode Go's latest DeepSeek V4 Flash at max is the implementation worker.
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
#   * Effort is explicit by role: review defaults to max; direct Codex
#     implement/consult calls default to high;
#     ultra remains refused because it is not a documented reasoning effort.
#   * implement requires explicit scope and an explicit plan-gate decision.
#     It snapshots HEAD plus every out-of-scope file/index entry, including
#     ignored files, and rejects scoped symlinks or secret-shaped descendants.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=write-scope.sh
. "$SCRIPT_DIR/write-scope.sh"

CODEX_IMPLEMENT_MODEL="${ORCHESTRA_CODEX_IMPLEMENT_MODEL:-}"
CODEX_REVIEW_MODEL="${ORCHESTRA_CODEX_REVIEW_MODEL:-gpt-5.6-luna}"

usage() {
  cat <<'EOF'
Usage:
  codex-agent.sh consult [--cd DIR] [--model MODEL] [--effort E] [--with-mcp] [--timeout N] -- "<prompt>"
  codex-agent.sh review  [--cd DIR] [--base REF|--commit SHA|--uncommitted] [--model MODEL] [--effort E] [--timeout N] [--prompt TEXT]
  codex-agent.sh implement --allow-write --scope PATH [--scope PATH]... (--plan-record FILE|--no-plan-gate) [--cd DIR] [--model MODEL] [--effort E] [--allow-main] [--timeout N] -- "<task>"

Defaults:
  consult    read-only codex exec, MCP off, effort floored to high, 900s timeout
  review     gpt-5.6-luna/max codex review --uncommitted, 1800s timeout
  implement  config-model/high workspace-write codex exec, 3600s timeout

Write scopes are required literal repository-relative path prefixes. The
wrapper snapshots Git refs/config/reflogs, the index, and all out-of-scope
filesystem entries (including ignored files and empty directories), tolerates
a dirty baseline, and fails if anything outside scope changes. It never
reverts changes. Scoped symlinks, external repository symlinks, and existing
secret-shaped descendants are refused. Use --scope . only for explicit
whole-repository authority.

Every implementation must explicitly choose --plan-record FILE for a selected
gate, or --no-plan-gate for a consciously ungated low-risk task. A plan record
needs: plan: P<n>, status: accepted, independent-review: complete, and
blocking-findings: none|resolved.

Timeout precedence: --timeout > CODEX_AGENT_TIMEOUT > per-mode default. 0 disables.
Model: consult/direct implement use Codex config unless overridden; review
defaults to gpt-5.6-luna. Override any call with --model.
Effort: --effort none|low|medium|high|xhigh|max wins. Review defaults to max;
direct implement/consult default to at least high. Ultra is refused.

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
# conductor forever. Uses timeout(1)/gtimeout(1) when present, else perl's
# alarm(2) (stock macOS has neither timeout nor gtimeout, but always has perl).
#
# Every path execs in the FOREGROUND with stdin closed. Both matter:
#   - Backgrounding the call breaks `codex exec`, which produced a silent
#     zero-byte exit 1 on stock macOS.
#   - `codex exec` treats a non-TTY stdin as extra prompt input, so an agent or
#     CI caller hangs forever on "Reading additional input from stdin...".
#     All three modes pass the prompt via argv, so nothing needs stdin.
run_bounded() {
  local seconds="$1"
  shift
  if [ -z "$seconds" ] || [ "$seconds" = "0" ]; then
    exec "$@" </dev/null
  elif command -v timeout >/dev/null 2>&1; then
    exec timeout "$seconds" "$@" </dev/null
  elif command -v gtimeout >/dev/null 2>&1; then
    exec gtimeout "$seconds" "$@" </dev/null
  elif command -v perl >/dev/null 2>&1; then
    # alarm() fires SIGALRM, which terminates the exec'd process; exit 142.
    exec perl -e 'my $t = shift; alarm $t; exec @ARGV or exit 127;' \
      "$seconds" "$@" </dev/null
  else
    echo "warning: no timeout, gtimeout, or perl found; running unbounded" >&2
    exec "$@" </dev/null
  fi
}

# Implement mode must inspect the working tree after Codex exits, so it cannot
# exec-replace this wrapper like consult/review do.
run_bounded_wait() {
  local seconds="$1"
  shift
  if [ -z "$seconds" ] || [ "$seconds" = "0" ]; then
    "$@" </dev/null
  elif command -v timeout >/dev/null 2>&1; then
    timeout "$seconds" "$@" </dev/null
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$seconds" "$@" </dev/null
  elif command -v perl >/dev/null 2>&1; then
    perl -e 'my $t = shift; alarm $t; exec @ARGV or exit 127;' \
      "$seconds" "$@" </dev/null
  else
    echo "warning: no timeout, gtimeout, or perl found; running unbounded" >&2
    "$@" </dev/null
  fi
}

# User policy: Go DeepSeek V4 Flash/max implements, Luna/max critiques,
# and Sol/xhigh overviews. This wrapper owns the two Codex stages; explicit
# per-call selection always wins.
validate_effort() {
  case "$1" in
    none|low|medium|high|xhigh|max) : ;;
    ultra) die "--effort ultra refused (not a documented Codex reasoning effort; use max)" ;;
    *) die "invalid --effort '$1' (use none, low, medium, high, xhigh, or max)" ;;
  esac
}

# Prints the mode default/floor, or nothing when an adequate config value stands.
effort_override() {
  # effort_override <mode>
  #
  # Reads the configured effort so consult/direct implement calls can floor
  # weak defaults to high. TOML
  # accepts single quotes, double quotes, or none, so capture the first
  # alphabetic run after '=' rather than assuming one quote style — a
  # double-quote-only pattern left `eff` holding the whole config line.
  #
  # Always returns 0. The `*)` branch used to end on a failed `[ ... ]` test,
  # which returned 1 for every non-consult mode; under `set -euo pipefail` that
  # killed the caller at `eff_ov="${effort:-$(effort_override implement)}"` with
  # no output and exit 1.
  local cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  local eff
  eff=$(grep -E '^[[:space:]]*model_reasoning_effort' "$cfg" 2>/dev/null | head -1 | sed -E 's/.*=[^A-Za-z]*([A-Za-z]+).*/\1/')
  case "$1" in
    review) printf 'max' ;;
    implement|consult)
      case "$eff" in
        high|xhigh|max) : ;;
        *) printf 'high' ;;
      esac
      ;;
  esac
  return 0
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
  local cd_dir="" model="$CODEX_REVIEW_MODEL" prompt="" target_kind="" target_value="" title="" timeout_flag="" effort=""
  local cmd=(codex review)
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --base|--commit)
        need_value "$1" "$#"
        [ -z "$target_kind" ] || die "choose exactly one review target"
        target_kind="${1#--}"
        target_value="$2"
        shift 2
        ;;
      --uncommitted)
        [ -z "$target_kind" ] || die "choose exactly one review target"
        target_kind=uncommitted
        shift
        ;;
      --title) need_value "$1" "$#"; title="$2"; shift 2 ;;
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

  [ -n "$target_kind" ] || target_kind=uncommitted
  [ -n "$model" ] && cmd+=(-c "model=\"$model\"")
  local eff_ov
  eff_ov="${effort:-$(effort_override review)}"
  [ -n "$eff_ov" ] && cmd+=(-c "model_reasoning_effort=\"$eff_ov\"")
  if [ -n "$prompt" ]; then
    check_prompt "$prompt"
    # Current Codex CLI releases reject a custom [PROMPT] combined with
    # --uncommitted, --base, or --commit even though the help text presents
    # them independently. Keep native `codex review`, but express the selected
    # target inside the custom instructions so role-specific critique and
    # overview prompts remain usable.
    local target_instruction
    case "$target_kind" in
      uncommitted)
        target_instruction='Review all staged, unstaged, and untracked changes in the current repository. Inspect the actual Git status and diffs; do not assume the working tree is clean.'
        ;;
      base)
        target_instruction="Review the changes in the current branch against base '$target_value'. Inspect the actual Git diff and repository evidence."
        ;;
      commit)
        target_instruction="Review the changes introduced by commit '$target_value'. Inspect the actual commit diff and repository evidence."
        ;;
      *) die "internal error: unknown review target '$target_kind'" ;;
    esac
    [ -z "$title" ] || target_instruction="$target_instruction
Review title: $title"
    cmd+=("$target_instruction

Additional review instructions:
$prompt")
  else
    case "$target_kind" in
      uncommitted) cmd+=(--uncommitted) ;;
      base) cmd+=(--base "$target_value") ;;
      commit) cmd+=(--commit "$target_value") ;;
      *) die "internal error: unknown review target '$target_kind'" ;;
    esac
    [ -z "$title" ] || cmd+=(--title "$title")
  fi

  echo "Codex review: model=${model:-config-default}; dir=$PWD; timeout=${timeout}s" >&2
  run_bounded "$timeout" "${cmd[@]}"
}

run_implement() {
  local cd_dir="$PWD" model="$CODEX_IMPLEMENT_MODEL" prompt="" allow_write=0 allow_main=0 timeout_flag="" effort=""
  local plan_record="" no_plan_gate=0 plan_id="" scope_state=""
  local scopes=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cd|-C) need_value "$1" "$#"; cd_dir="$2"; shift 2 ;;
      --model|-m) need_value "$1" "$#"; model="$2"; shift 2 ;;
      --effort) need_value "$1" "$#"; validate_effort "$2"; effort="$2"; shift 2 ;;
      --scope) need_value "$1" "$#"; scopes+=("$2"); shift 2 ;;
      --plan-record) need_value "$1" "$#"; plan_record="$2"; shift 2 ;;
      --no-plan-gate) no_plan_gate=1; shift ;;
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
  [ "${#scopes[@]}" -gt 0 ] || die "implementation requires at least one explicit --scope (use --scope . for the whole repository)"
  if [ -n "$plan_record" ] && [ "$no_plan_gate" -eq 1 ]; then
    die "choose exactly one of --plan-record FILE or --no-plan-gate"
  fi
  if [ -z "$plan_record" ] && [ "$no_plan_gate" -eq 0 ]; then
    die "implementation requires an explicit gate decision: --plan-record FILE or --no-plan-gate"
  fi
  [ -z "$plan_record" ] || plan_id="$(orchestra_validate_plan_record "$plan_record")" || exit $?
  [ -d "$cd_dir" ] || die "directory not found: $cd_dir"
  check_prompt "$prompt"
  ensure_codex
  # workspace-write outside version control has no diff/rollback story; refuse.
  is_git_repo "$cd_dir" || die "refusing workspace-write outside a git repository: $cd_dir"
  cd_dir="$(git -C "$cd_dir" rev-parse --show-toplevel)" || die "could not resolve repository root: $cd_dir"
  cd_dir="$(cd "$cd_dir" && pwd -P)" || die "could not canonicalize repository root: $cd_dir"

  local branch
  branch="$(current_branch "$cd_dir")"
  case "$branch" in
    main|master)
      [ "$allow_main" -eq 1 ] || die "refusing workspace-write on branch '$branch'; create/switch to a working branch or pass --allow-main explicitly"
      ;;
  esac

  local timeout
  timeout="$(resolve_timeout "$timeout_flag" 3600)"

  local scope normalized_scope
  local normalized_scopes=()
  for scope in "${scopes[@]}"; do
    normalized_scope="$(orchestra_normalize_scope "$scope")" || exit $?
    normalized_scopes+=("$normalized_scope")
  done
  scopes=("${normalized_scopes[@]}")
  orchestra_validate_scope_tree "$cd_dir" "${scopes[@]}" || exit $?

  scope_state="$(mktemp -d "${TMPDIR:-/tmp}/orchestra-scope-state.XXXXXX")" || die "could not create scope snapshot"
  ORCHESTRA_SCOPE_STATE="$scope_state"
  trap 'orchestra_scope_snapshot_destroy "${ORCHESTRA_SCOPE_STATE:-}"' EXIT
  orchestra_scope_snapshot_create "$cd_dir" "$scope_state" "${scopes[@]}" || exit $?

  local scope_text="Only modify these literal repository-relative path prefixes. If the task requires anything else, stop without editing outside them:"
  for scope in "${scopes[@]}"; do
    scope_text="$scope_text
- $scope"
  done

  local gate_text="No plan gate was selected for this low-risk task."
  [ -z "$plan_id" ] || gate_text="The conductor accepted $plan_id; implement only that accepted plan."

  local guarded_prompt
  guarded_prompt="You are Codex running as a bounded implementation agent.

Task:
$prompt

Scope:
$scope_text

Gate:
$gate_text

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
  local run_status=0 scope_status=0
  run_bounded_wait "$timeout" "${cmd[@]}" || run_status=$?
  orchestra_scope_snapshot_verify "$cd_dir" "$scope_state" "after delegation" "${scopes[@]}" || scope_status=$?
  orchestra_scope_snapshot_destroy "$scope_state" || true
  ORCHESTRA_SCOPE_STATE=""

  echo >&2
  echo "Working-tree changes (review the diff before accepting):" >&2
  git -C "$cd_dir" status --porcelain >&2 || true

  if [ "$scope_status" -eq 1 ]; then
    echo "error: Codex changed repository state outside --scope" >&2
    return 3
  fi
  if [ "$scope_status" -ne 0 ]; then
    echo "error: Codex scope enforcement could not inspect the final repository state" >&2
    return 4
  fi
  return "$run_status"
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
