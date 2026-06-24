#!/usr/bin/env bash
# consult-opencode.sh - invoke OpenCode as a read-only advisory consultant.
#
# Usage: consult-opencode.sh --model provider/model [--dir <repo>] "<prompt>"
# Exit:  0 = OpenCode replied, 2 = usage/precondition error, other = opencode.
#
# Safety:
#   * Requires an explicit model, either --model or OPENCODE_CONSULT_MODEL.
#   * Uses an inline OpenCode agent that denies edits, bash, web, tasks,
#     external directories, skill calls, and questions.
#   * OpenCode output is untrusted. The caller verifies and implements.

set -uo pipefail

MODEL="${OPENCODE_CONSULT_MODEL:-}"
DIR=""
VARIANT=""
TITLE=""
FORMAT=""
PROMPT=""
FILES=()
FILE_COUNT=0

usage() {
  sed -n '2,20p' "$0"
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
[ -n "$MODEL" ] || die "no model given; pass --model provider/model or set OPENCODE_CONSULT_MODEL"
case "$MODEL" in
  */*) : ;;
  *) die "model must use OpenCode provider/model form, for example anthropic/claude-sonnet-4-5" ;;
esac

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

readonly_permissions='{"*":"deny","read":"allow","glob":"allow","grep":"allow","list":"allow","edit":"deny","bash":"deny","task":"deny","external_directory":"deny","todowrite":"deny","webfetch":"deny","websearch":"deny","lsp":"deny","skill":"deny","question":"deny","doom_loop":"deny"}'
readonly_config='{"permission":{"*":"deny","read":"allow","glob":"allow","grep":"allow","list":"allow","edit":"deny","bash":"deny","task":"deny","external_directory":"deny","todowrite":"deny","webfetch":"deny","websearch":"deny","lsp":"deny","skill":"deny","question":"deny","doom_loop":"deny"},"agent":{"consult-opencode":{"description":"Read-only advisory consultant for code review, audits, planning, architecture, and hard bugs.","mode":"primary","permission":{"*":"deny","read":"allow","glob":"allow","grep":"allow","list":"allow","edit":"deny","bash":"deny","task":"deny","external_directory":"deny","todowrite":"deny","webfetch":"deny","websearch":"deny","lsp":"deny","skill":"deny","question":"deny","doom_loop":"deny"},"prompt":"You are a read-only advisory consultant. Analyze the provided repository context, prompt, files, and excerpts. Do not request or perform edits, shell commands, web access, subagent calls, or external-directory access. Provide concrete findings, risks, tradeoffs, and recommendations. Your response is advisory only; the calling agent will verify and implement any accepted changes."}},"share":"disabled"}'

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

echo "Consulting OpenCode (read-only agent; model=$MODEL; dir=$DIR)..." >&2
echo "opencode --pure run --agent consult-opencode --model $MODEL --dir $DIR <prompt>" >&2

export OPENCODE_CONFIG_CONTENT="$readonly_config"
export OPENCODE_PERMISSION="$readonly_permissions"
export OPENCODE_DISABLE_CLAUDE_CODE=1
export OPENCODE_DISABLE_DEFAULT_PLUGINS=1
export OPENCODE_DISABLE_AUTOUPDATE=1
export OPENCODE_AUTO_SHARE=false

exec "${cmd[@]}"
