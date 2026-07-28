#!/usr/bin/env bash
# consult-opencode.sh - invoke OpenCode as a read-only advisory consultant.
# Canonical Agent Orchestra copy; the deprecated opencode-consult skill forwards here.
#
# Usage: consult-opencode.sh (--lane LANE | --model provider/model) [options] "<prompt>"
#   --lane LANE         Shortcut for the standard delegation lanes:
#                         code      -> openrouter/moonshotai/kimi-k2.7-code
#                         reasoning -> openrouter/minimax/minimax-m3 (high reasoning)
#                         context   -> openrouter/deepseek/deepseek-v4-flash (cheap, ~1M ctx)
#                         prose     -> openrouter/xiaomi/mimo-v2.5-pro
#                       Override per-lane via ORCHESTRA_LANE_CODE / _REASONING /
#                       _CONTEXT / _PROSE.
#   --model M           Explicit provider/model (wins if given after --lane).
#   --reasoning EFFORT  OpenRouter reasoning effort: low|medium|high. Defaults to
#                       high for the reasoning lane, unset otherwise. OpenRouter
#                       models only; ignored for other providers.
#   --sealed            Deny file access too (read/glob/grep/list). Use when all
#                       context is inline; removes exploratory tool round-trips.
#   --timeout SECONDS   Fail fast if the provider stalls (default 240; 0 = none).
#   --quant a,b         Pin OpenRouter quantizations (e.g. fp8,bf16) for quality.
#   --max-tokens N      Cap output tokens (OpenRouter models; experimental).
#   --dir <repo>        Working directory (default: PWD).
#   --file <path>       Attach a file (repeatable).
#   --json              JSON output format.
# Exit:  0 = OpenCode replied, 2 = usage/precondition error, 124+ = timeout,
#        other = opencode.
#
# Safety:
#   * Requires an explicit model, via --lane, --model, or OPENCODE_CONSULT_MODEL.
#   * Uses an inline OpenCode agent that denies edits, bash, web, tasks,
#     external directories, skill calls, and questions. --sealed also denies
#     file reads/search so the model judges only the inline material.
#   * Non-sealed mode can read ANY file under --dir, including untracked
#     .env files; the secret guards screen only the prompt and attached
#     filenames. Use --sealed or a clean tree for secret-adjacent repos.
#   * OpenRouter models get pinned provider routing (throughput + require
#     parameters) to avoid slow, low-quant backends.
#   * OpenCode output is untrusted. The caller verifies and implements.
#   * Run lanes sequentially: OpenCode shares one SQLite DB and concurrent runs
#     can fail with "database is locked".

set -uo pipefail

LANE_CODE="${ORCHESTRA_LANE_CODE:-openrouter/moonshotai/kimi-k2.7-code}"
LANE_PROSE="${ORCHESTRA_LANE_PROSE:-openrouter/xiaomi/mimo-v2.5-pro}"
LANE_REASONING="${ORCHESTRA_LANE_REASONING:-openrouter/minimax/minimax-m3}"
LANE_CONTEXT="${ORCHESTRA_LANE_CONTEXT:-openrouter/deepseek/deepseek-v4-flash}"

MODEL="${OPENCODE_CONSULT_MODEL:-}"
REASONING=""
REASONING_DEFAULT=""
DIR=""
VARIANT=""
TITLE=""
FORMAT=""
PROMPT=""
FILES=()
FILE_COUNT=0
SEALED=""
TIMEOUT="${OPENCODE_CONSULT_TIMEOUT:-240}"
QUANT=""
MAX_TOKENS=""

usage() {
  sed -n '2,40p' "$0"
}

die() {
  echo "error: $*" >&2
  exit 2
}

append_prompt_word() {
  if [ -z "$PROMPT" ]; then
    PROMPT="$1"
  else
    PROMPT="$PROMPT $1"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir|--cd)
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
      [ "$#" -ge 2 ] || die "--lane requires one of: code, reasoning, context, prose"
      case "$2" in
        code) MODEL="$LANE_CODE" ;;
        prose|writing) MODEL="$LANE_PROSE" ;;
        reasoning|architecture) MODEL="$LANE_REASONING"; REASONING_DEFAULT="high" ;;
        context|longcontext) MODEL="$LANE_CONTEXT" ;;
        *) die "unknown lane '$2' (use code, reasoning, context, or prose)" ;;
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
    --variant)
      [ "$#" -ge 2 ] || die "--variant requires a value"
      VARIANT="$2"
      shift 2
      ;;
    --title)
      [ "$#" -ge 2 ] || die "--title requires a value"
      TITLE="$2"
      shift 2
      ;;
    --file|-f)
      [ "$#" -ge 2 ] || die "$1 requires a file path"
      FILES+=("$2")
      FILE_COUNT=$((FILE_COUNT + 1))
      shift 2
      ;;
    --sealed)
      SEALED=1
      shift
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
    --max-tokens)
      [ "$#" -ge 2 ] || die "--max-tokens requires a number"
      MAX_TOKENS="$2"
      shift 2
      ;;
    --json)
      FORMAT="json"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        append_prompt_word "$1"
        shift
      done
      ;;
    -*)
      die "unknown flag: $1"
      ;;
    *)
      append_prompt_word "$1"
      shift
      ;;
  esac
done

[ -n "$PROMPT" ] || die "no prompt given"
[ -n "$MODEL" ] || die "no model given; pass --lane code|reasoning|context|prose, --model provider/model, or set OPENCODE_CONSULT_MODEL"
case "$MODEL" in
  */*) : ;;
  *) die "model must use OpenCode provider/model form, for example openrouter/moonshotai/kimi-k2.7-code" ;;
esac

# Reasoning effort: explicit --reasoning wins; otherwise the lane default
# (high for the MiniMax reasoning lane). Only applied to OpenRouter models.
REASONING="${REASONING:-$REASONING_DEFAULT}"

[ -n "$DIR" ] || DIR="$PWD"
[ -d "$DIR" ] || die "directory not found: $DIR"

secret_re='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|github_pat_|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|password[[:space:]]*[:=]|api[_ -]?key[[:space:]]*[:=]|token[[:space:]]*[:=]'
if printf '%s' "$PROMPT" | grep -qiE "$secret_re"; then
  die "prompt appears to contain a secret; redact before consulting OpenCode"
fi

if [ "$FILE_COUNT" -gt 0 ]; then
  for file in "${FILES[@]}"; do
    [ -f "$file" ] || die "attached file not found: $file"
    base=$(basename "$file" | tr '[:upper:]' '[:lower:]')
    case "$base" in
      .env|.env.*|id_rsa|id_dsa|id_ecdsa|id_ed25519|*.pem|*.key|*.p12|*.pfx|*secret*|*credential*|*token*)
        die "refusing to attach likely secret-bearing file: $file"
        ;;
    esac
  done
fi

if ! command -v opencode >/dev/null 2>&1; then
  die "'opencode' CLI not found on PATH; install/authenticate OpenCode, or skip the consult"
fi

# Always pass an explicit session title. Without one, OpenCode auto-generates a
# title with its default small model, an extra billed side-call per consult.
TITLE="${TITLE:-consult}"

# Sealed mode denies file reads/search too, so the model judges only the inline
# material — no exploratory tool round-trips, and no unrelated repo context to
# muddy a bounded review.
if [ -n "$SEALED" ]; then
  fileperms='"read":"deny","glob":"deny","grep":"deny","list":"deny"'
  agent_prompt='You are a read-only advisory consultant in SEALED mode. Every piece of context you need is provided inline in the prompt. You have no file, glob, grep, list, web, shell, task, or directory access and must not request any. Review only the inline material against the stated source wording. Be concrete: for each issue give the exact quote, the problem, the correction, and one line of reasoning. Your response is advisory only and the calling agent will verify it.'
else
  fileperms='"read":"allow","glob":"allow","grep":"allow","list":"allow"'
  agent_prompt='You are a read-only advisory consultant. Analyze the provided repository context, prompt, files, and excerpts. Do not request or perform edits, shell commands, web access, subagent calls, or external-directory access. Provide concrete findings, risks, tradeoffs, and recommendations. Your response is advisory only; the calling agent will verify and implement any accepted changes.'
fi

permmap="{\"*\":\"deny\",${fileperms},\"edit\":\"deny\",\"bash\":\"deny\",\"task\":\"deny\",\"external_directory\":\"deny\",\"todowrite\":\"deny\",\"webfetch\":\"deny\",\"websearch\":\"deny\",\"lsp\":\"deny\",\"skill\":\"deny\",\"question\":\"deny\",\"doom_loop\":\"deny\"}"

# Pin OpenRouter routing so the call lands on a fast, full-precision backend
# instead of whatever cheap, heavily-quantized provider is momentarily cheapest.
# allow_fallbacks stays true so pinning never turns into a dead "no provider" call.
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
    [ -n "$MAX_TOKENS" ] && optbody="$optbody,\"max_tokens\":$MAX_TOKENS"
    [ -n "$REASONING" ] && optbody="$optbody,\"reasoning\":{\"effort\":\"$REASONING\"}"
    provider_block=",\"provider\":{\"openrouter\":{\"models\":{\"$model_id\":{\"options\":{$optbody}}}}}"
    ;;
esac

readonly_permissions="$permmap"
readonly_config="{\"permission\":$permmap,\"agent\":{\"consult-opencode\":{\"description\":\"Read-only advisory consultant for code review, audits, planning, architecture, and hard bugs.\",\"mode\":\"primary\",\"permission\":$permmap,\"prompt\":\"$agent_prompt\"}},\"share\":\"disabled\"$provider_block}"

cmd=(opencode --pure run --agent consult-opencode --model "$MODEL" --dir "$DIR")
[ -n "$VARIANT" ] && cmd+=(--variant "$VARIANT")
[ -n "$TITLE" ] && cmd+=(--title "$TITLE")
[ -n "$FORMAT" ] && cmd+=(--format "$FORMAT")
if [ "$FILE_COUNT" -gt 0 ]; then
  for file in "${FILES[@]}"; do
    cmd+=(--file "$file")
  done
fi
cmd+=(-- "$PROMPT")

mode="standard"; [ -n "$SEALED" ] && mode="sealed"
echo "Consulting OpenCode (read-only $mode agent; model=$MODEL; reasoning=${REASONING:-provider-default}; dir=$DIR; timeout=${TIMEOUT}s)..." >&2
echo "opencode --pure run --agent consult-opencode --model $MODEL --dir $DIR <prompt>" >&2

export OPENCODE_CONFIG_CONTENT="$readonly_config"
export OPENCODE_PERMISSION="$readonly_permissions"
export OPENCODE_DISABLE_CLAUDE_CODE=1
export OPENCODE_DISABLE_DEFAULT_PLUGINS=1
export OPENCODE_DISABLE_AUTOUPDATE=1
export OPENCODE_AUTO_SHARE=false

# Bounded execution: a stalled provider fails fast instead of hanging forever.
# Every path execs in the FOREGROUND with stdin closed. Backgrounding the call
# made a sealed consult return zero bytes on stock macOS, which has neither
# timeout(1) nor gtimeout(1); perl is always present and alarm(2) bounds the
# call without giving up the foreground. The prompt travels in argv, so nothing
# here needs stdin, and leaving it open lets a non-TTY caller hang.
if [ -z "$TIMEOUT" ] || [ "$TIMEOUT" = "0" ]; then
  exec "${cmd[@]}" </dev/null
elif command -v timeout >/dev/null 2>&1; then
  exec timeout "$TIMEOUT" "${cmd[@]}" </dev/null
elif command -v gtimeout >/dev/null 2>&1; then
  exec gtimeout "$TIMEOUT" "${cmd[@]}" </dev/null
elif command -v perl >/dev/null 2>&1; then
  # alarm() fires SIGALRM, which terminates the exec'd process; exit 142.
  exec perl -e 'my $t = shift; alarm $t; exec @ARGV or exit 127;' \
    "$TIMEOUT" "${cmd[@]}" </dev/null
else
  echo "warning: no timeout, gtimeout, or perl found; running unbounded" >&2
  exec "${cmd[@]}" </dev/null
fi
