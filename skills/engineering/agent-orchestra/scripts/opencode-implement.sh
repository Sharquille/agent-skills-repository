#!/usr/bin/env bash
# opencode-implement.sh - guarded write-capable OpenCode lane for bounded
# implementation. This is the fallback when Codex cannot continue (rate limit,
# auth, outage): delegate the bulk code-writing to an open model so Claude
# quota is still preserved.
#
# Usage: opencode-implement.sh --allow-write [options] -- "<task>"
#   --allow-write       REQUIRED. Explicit opt-in to file edits.
#   --cd|--dir DIR      Target git repository (default: PWD). Must be a git
#                       repo on a non-main branch (or pass --allow-main).
#   --lane LANE         code (default, Kimi K2.7 Code), reasoning (MiniMax M3,
#                       high reasoning; hard tasks), or context (DeepSeek V4
#                       Flash, cheap ~1M ctx; long-context bulk edits).
#   --model M           Explicit provider/model override.
#   --reasoning EFFORT  OpenRouter reasoning effort: low|medium|high.
#   --scope PATH        Restrict edits to PATH (repeatable, enforced in-prompt).
#   --allow-main        Permit running on main/master (off by default).
#   --timeout SECONDS   Bound the run (default 3600; 0 = none).
#   --quant a,b         Pin OpenRouter quantizations.
# Exit:  0 = run completed, 2 = usage/precondition error, 124+ = timeout.
#
# Safety (do not weaken):
#   * The inline agent may READ and EDIT files only. bash, web, tasks, skills,
#     and external directories are denied — it structurally cannot run
#     commands, commit, push, or exfiltrate. The conductor runs tests.
#   * Requires a git repo and refuses main/master without --allow-main, so
#     every change is diffable and revertable (git diff / git checkout).
#   * Secret guard on the task text; the agent is instructed away from
#     secret-bearing files (and .env etc. remain untracked/denied by scope).
#   * Prints the resulting git status after the run so the caller immediately
#     sees what changed. All output is untrusted; review the diff.

set -uo pipefail

LANE_CODE="${ORCHESTRA_LANE_CODE:-openrouter/moonshotai/kimi-k2.7-code}"
LANE_REASONING="${ORCHESTRA_LANE_REASONING:-openrouter/minimax/minimax-m3}"
LANE_CONTEXT="${ORCHESTRA_LANE_CONTEXT:-openrouter/deepseek/deepseek-v4-flash}"

MODEL="${ORCHESTRA_IMPLEMENT_MODEL:-$LANE_CODE}"
DIR="$PWD"
PROMPT=""
ALLOW_WRITE=0
ALLOW_MAIN=0
TIMEOUT="${OPENCODE_IMPLEMENT_TIMEOUT:-3600}"
QUANT=""
REASONING=""
SCOPES=()
SCOPE_COUNT=0

usage() {
  sed -n '2,31p' "$0"
}

die() {
  echo "error: $*" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cd|--dir|-C)
      [ "$#" -ge 2 ] || die "$1 requires a directory"
      DIR="$2"
      shift 2
      ;;
    --model|-m)
      [ "$#" -ge 2 ] || die "$1 requires a provider/model value"
      MODEL="$2"
      shift 2
      ;;
    --lane)
      [ "$#" -ge 2 ] || die "--lane requires code, reasoning, or context"
      case "$2" in
        code) MODEL="$LANE_CODE" ;;
        reasoning) MODEL="$LANE_REASONING"; REASONING="${REASONING:-high}" ;;
        context) MODEL="$LANE_CONTEXT" ;;
        *) die "unknown implement lane '$2' (use code, reasoning, or context)" ;;
      esac
      shift 2
      ;;
    --reasoning)
      [ "$#" -ge 2 ] || die "--reasoning requires low, medium, or high"
      case "$2" in
        low|medium|high) REASONING="$2" ;;
        *) die "invalid reasoning effort '$2' (use low, medium, or high)" ;;
      esac
      shift 2
      ;;
    --scope)
      [ "$#" -ge 2 ] || die "--scope requires a path"
      [ -n "$2" ] || die "--scope requires a non-empty path"
      SCOPES+=("$2")
      SCOPE_COUNT=$((SCOPE_COUNT + 1))
      shift 2
      ;;
    --timeout)
      [ "$#" -ge 2 ] || die "--timeout requires a value in seconds"
      TIMEOUT="$2"
      shift 2
      ;;
    --quant)
      [ "$#" -ge 2 ] || die "--quant requires a comma-separated list"
      QUANT="$2"
      shift 2
      ;;
    --allow-write) ALLOW_WRITE=1; shift ;;
    --allow-main) ALLOW_MAIN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --)
      shift
      PROMPT="$*"
      break
      ;;
    -*) die "unknown flag: $1" ;;
    *)
      if [ -z "$PROMPT" ]; then PROMPT="$1"; else PROMPT="$PROMPT $1"; fi
      shift
      ;;
  esac
done

[ "$ALLOW_WRITE" -eq 1 ] || die "implementation requires --allow-write"
[ -n "$PROMPT" ] || die "no task given"
[ -d "$DIR" ] || die "directory not found: $DIR"
case "$MODEL" in
  */*) : ;;
  *) die "model must use OpenCode provider/model form" ;;
esac

git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1 || die "refusing write mode outside a git repository: $DIR"
branch="$(git -C "$DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
case "$branch" in
  main|master)
    [ "$ALLOW_MAIN" -eq 1 ] || die "refusing write mode on branch '$branch'; create/switch to a working branch or pass --allow-main explicitly"
    ;;
esac

secret_re='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|github_pat_|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|password[[:space:]]*[:=]|api[_ -]?key[[:space:]]*[:=]|token[[:space:]]*[:=]'
if printf '%s' "$PROMPT" | grep -qiE "$secret_re"; then
  die "task appears to contain a secret; redact before delegating"
fi

command -v opencode >/dev/null 2>&1 || die "'opencode' CLI not found on PATH"

scope_text="No explicit scope paths were provided. Infer the minimal safe scope from the task."
if [ "$SCOPE_COUNT" -gt 0 ]; then
  scope_text="Only modify these paths unless the task is impossible without expanding scope:"
  for scope in "${SCOPES[@]}"; do
    scope_text="$scope_text
- $scope"
  done
fi

guarded_prompt="You are a bounded implementation agent with file read and edit tools ONLY. You have no shell, no web access, no subagents, and no access outside this repository. You cannot run commands, tests, git, or builds — do not claim to have run anything.

Task:
$PROMPT

Scope:
$scope_text

Rules:
- Make the smallest correct change.
- Do not create commits, and do not modify anything under .git/.
- Do not read or modify secret-bearing files such as .env, private keys, tokens, or credential stores.
- Match the style and conventions of the surrounding code.
- Finish with: a list of every file you changed and why, what you could NOT verify (you cannot execute anything), and any residual risks the caller must check."

# Edit-capable but shell-less agent: read/search/edit tools allowed, everything
# else denied (catch-all deny covers unknown/new tools).
permmap='{"*":"deny","read":"allow","glob":"allow","grep":"allow","list":"allow","edit":"allow","write":"allow","patch":"allow","bash":"deny","task":"deny","external_directory":"deny","todowrite":"deny","webfetch":"deny","websearch":"deny","lsp":"deny","skill":"deny","question":"deny","doom_loop":"deny"}'

agent_prompt='You are a bounded implementation agent. You may read, search, and edit files in this repository only. You have no shell, web, task, or external access and must not request any. Make the smallest correct change for the stated task, stay inside the stated scope, never touch secret-bearing files, and end with a summary of changed files, unverified assumptions, and residual risks.'

# Pin OpenRouter routing to fast full-precision backends; optionally set
# reasoning effort (MiniMax reasoning lane defaults to high).
provider_block=""
case "$MODEL" in
  openrouter/*)
    model_id="${MODEL#openrouter/}"
    routing='"sort":"throughput","require_parameters":true,"allow_fallbacks":true'
    if [ -n "$QUANT" ]; then
      qjson=$(printf '%s' "$QUANT" | awk -F, '{o="";for(i=1;i<=NF;i++){gsub(/^ +| +$/,"",$i);o=o (i>1?",":"") "\"" $i "\""};print o}')
      routing="$routing,\"quantizations\":[$qjson]"
    fi
    optbody="\"provider\":{$routing}"
    [ -n "$REASONING" ] && optbody="$optbody,\"reasoning\":{\"effort\":\"$REASONING\"}"
    provider_block=",\"provider\":{\"openrouter\":{\"models\":{\"$model_id\":{\"options\":{$optbody}}}}}"
    ;;
esac

implement_config="{\"permission\":$permmap,\"agent\":{\"implement-opencode\":{\"description\":\"Bounded implementation agent: file edits only, no shell.\",\"mode\":\"primary\",\"permission\":$permmap,\"prompt\":\"$agent_prompt\"}},\"share\":\"disabled\"$provider_block}"

cmd=(opencode --pure run --agent implement-opencode --model "$MODEL" --dir "$DIR" --title implement -- "$guarded_prompt")

echo "OpenCode implementation: edit-only agent (no shell); model=$MODEL; reasoning=${REASONING:-provider-default}; dir=$DIR; branch=${branch:-unknown}; timeout=${TIMEOUT}s" >&2

export OPENCODE_CONFIG_CONTENT="$implement_config"
export OPENCODE_PERMISSION="$permmap"
export OPENCODE_DISABLE_CLAUDE_CODE=1
export OPENCODE_DISABLE_DEFAULT_PLUGINS=1
export OPENCODE_DISABLE_AUTOUPDATE=1
export OPENCODE_AUTO_SHARE=false

# Bounded execution, then show what actually changed on disk. This cannot exec:
# the working-tree report below has to run afterwards. Each path still runs in
# the FOREGROUND with stdin closed — backgrounding the call returned zero bytes
# on stock macOS, which ships neither timeout(1) nor gtimeout(1), and an open
# non-TTY stdin lets the provider block waiting for input it will never get.
run_status=0
if [ -z "$TIMEOUT" ] || [ "$TIMEOUT" = "0" ]; then
  "${cmd[@]}" </dev/null || run_status=$?
elif command -v timeout >/dev/null 2>&1; then
  timeout "$TIMEOUT" "${cmd[@]}" </dev/null || run_status=$?
elif command -v gtimeout >/dev/null 2>&1; then
  gtimeout "$TIMEOUT" "${cmd[@]}" </dev/null || run_status=$?
elif command -v perl >/dev/null 2>&1; then
  # alarm() fires SIGALRM, which terminates the child; run_status becomes 142.
  perl -e 'my $t = shift; alarm $t; exec @ARGV or exit 127;' \
    "$TIMEOUT" "${cmd[@]}" </dev/null || run_status=$?
  [ "$run_status" -gt 128 ] && echo "error: implementation exceeded ${TIMEOUT}s and was terminated" >&2
else
  echo "warning: no timeout, gtimeout, or perl found; running unbounded" >&2
  "${cmd[@]}" </dev/null || run_status=$?
fi

echo >&2
echo "Working-tree changes (review the diff before accepting):" >&2
git -C "$DIR" status --porcelain >&2 || true
exit "$run_status"
