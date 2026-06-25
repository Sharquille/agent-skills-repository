#!/usr/bin/env bash
# consult-panel.sh - run the two-lane study consult panel.
#
# The technical lane (default Kimi K2.7 Code) and the writing lane (default MiMo
# v2.5 Pro) each run SEALED (no repo access; all context inline) and time-bounded
# via the audited opencode-consult wrapper. Both results are printed labeled for
# the calling agent to reconcile against the source.
#
# Sequential by default: opencode shares one SQLite DB, so concurrent runs can
# fail with "database is locked". Sealed mode already makes each lane fast
# (~30-40s), so sequential is reliable and quick. --parallel is opt-in.
#
# Independent-before-shared: each lane sees only its own prompt, never the other
# model's answer. The calling agent owns the verdict and writes the note.
#
# Usage:
#   consult-panel.sh --tech-prompt FILE --write-prompt FILE \
#     [--tech-model M] [--write-model M] [--timeout N] [--quant a,b] \
#     [--dir D] [--parallel]
#
# Exit: 0 if both lanes returned; non-zero if either lane failed/timed out.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WRAPPER="$(cd "$SCRIPT_DIR/../../opencode-consult/scripts" 2>/dev/null && pwd)/consult-opencode.sh"

TECH_MODEL="openrouter/moonshotai/kimi-k2.7-code"
WRITE_MODEL="openrouter/xiaomi/mimo-v2.5-pro"
TECH_PROMPT=""
WRITE_PROMPT=""
TIMEOUT="240"
QUANT=""
DIR="$PWD"
PARALLEL=""

die() { echo "error: $*" >&2; exit 2; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tech-prompt)  TECH_PROMPT="$2"; shift 2 ;;
    --write-prompt) WRITE_PROMPT="$2"; shift 2 ;;
    --tech-model)   TECH_MODEL="$2"; shift 2 ;;
    --write-model)  WRITE_MODEL="$2"; shift 2 ;;
    --timeout)      TIMEOUT="$2"; shift 2 ;;
    --quant)        QUANT="$2"; shift 2 ;;
    --dir)          DIR="$2"; shift 2 ;;
    --parallel)     PARALLEL=1; shift ;;
    -h|--help)      sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -x "$WRAPPER" ] || die "consult-opencode.sh wrapper not found/executable at: $WRAPPER"
[ -n "$TECH_PROMPT" ] && [ -f "$TECH_PROMPT" ] || die "--tech-prompt FILE is required and must exist"
[ -n "$WRITE_PROMPT" ] && [ -f "$WRITE_PROMPT" ] || die "--write-prompt FILE is required and must exist"

quant_arg=()
[ -n "$QUANT" ] && quant_arg=(--quant "$QUANT")

tech_out="$(mktemp)"
write_out="$(mktemp)"
trap 'rm -f "$tech_out" "$write_out"' EXIT

# bash 3.2 (stock macOS) errors on "${arr[@]}" when the array is empty under
# `set -u`; the ${arr[@]+...} guard expands to nothing safely.
run_lane() { # <model> <prompt-file> <out-file>
  "$WRAPPER" --sealed --timeout "$TIMEOUT" ${quant_arg[@]+"${quant_arg[@]}"} \
    --dir "$DIR" --model "$1" -- "$(cat "$2")" >"$3" 2>&1
}

mode="sequential"; [ -n "$PARALLEL" ] && mode="parallel"
echo "Panel: technical=$TECH_MODEL | writing=$WRITE_MODEL | sealed | timeout=${TIMEOUT}s | $mode" >&2

if [ -n "$PARALLEL" ]; then
  # Opt-in only: opencode shares one SQLite DB, so concurrent runs can fail with
  # "database is locked". Default is sequential for reliability.
  run_lane "$TECH_MODEL" "$TECH_PROMPT" "$tech_out" &
  tpid=$!
  run_lane "$WRITE_MODEL" "$WRITE_PROMPT" "$write_out" &
  wpid=$!
  wait "$tpid"; tstat=$?
  wait "$wpid"; wstat=$?
else
  run_lane "$TECH_MODEL" "$TECH_PROMPT" "$tech_out"; tstat=$?
  run_lane "$WRITE_MODEL" "$WRITE_PROMPT" "$write_out"; wstat=$?
fi

echo "===== TECHNICAL LANE — $TECH_MODEL (exit $tstat) ====="
cat "$tech_out"
echo
echo "===== WRITING LANE — $WRITE_MODEL (exit $wstat) ====="
cat "$write_out"

[ "$tstat" -eq 0 ] && [ "$wstat" -eq 0 ] || exit 1
