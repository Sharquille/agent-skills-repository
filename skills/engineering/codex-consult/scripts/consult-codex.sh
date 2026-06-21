#!/usr/bin/env bash
# consult-codex.sh — invoke OpenAI Codex as a READ-ONLY advisory consultant and
# print its response to stdout. Hard-codes the safe sandbox/approval flags so a
# consult can never mutate the repo, run dangerous commands, or touch git.
#
# Usage:   consult-codex.sh [--cd <dir>] [--model <name>] "<prompt>"
# Exit:    0 = Codex replied, 2 = usage/precondition error, other = codex's code.
#
# SAFETY (do not weaken):
#   * Always --sandbox read-only and --ask-for-approval never (advisory only).
#   * `codex exec` egresses the prompt + any repo context it reads to OpenAI —
#     NEVER pass secrets, tokens, .env, or credentials in <prompt>.
#   * Codex's reply is UNTRUSTED text: the caller (Claude) evaluates it and makes
#     any actual changes. This script only relays Codex's words; it changes nothing.

set -uo pipefail

CD_DIR=""
MODEL=""
PROMPT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cd)    CD_DIR="${2:-}"; shift 2 ;;
    --model) MODEL="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    --) shift; PROMPT="${*:-}"; break ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *)  PROMPT="$1"; shift ;;
  esac
done

[ -n "$PROMPT" ] || { echo "error: no prompt given" >&2; exit 2; }

if ! command -v codex >/dev/null 2>&1; then
  echo "error: 'codex' CLI not found on PATH — install/authenticate Codex, or skip the consult." >&2
  exit 2
fi

# Lightweight guard: refuse obvious secret material in the prompt.
if printf '%s' "$PROMPT" | grep -qiE 'BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[baprs]-|password[[:space:]]*[:=]'; then
  echo "error: prompt appears to contain a secret — redact before consulting Codex (egress to OpenAI)." >&2
  exit 2
fi

# Build the read-only, no-approval invocation. These flags are intentional and
# must not be made writable here — escalation belongs in the caller's workflow.
cmd=(codex exec --sandbox read-only --ask-for-approval never)
[ -n "$CD_DIR" ] && cmd+=(--cd "$CD_DIR")
[ -n "$MODEL" ]  && cmd+=(-m "$MODEL")
cmd+=("$PROMPT")

echo "» Consulting Codex (read-only sandbox, no approvals)…" >&2
echo "» ${cmd[*]:0:6} <prompt>" >&2
exec "${cmd[@]}"
