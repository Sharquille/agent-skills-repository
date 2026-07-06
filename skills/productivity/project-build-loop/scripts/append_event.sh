#!/usr/bin/env bash
# append_event.sh - append one JSON event to a project's event-log.jsonl with a
# correct monotonically-increasing seq. Single source of truth for event writes
# (used directly and by the gate-receipt paths in policy_check.sh/secret_scan.sh).
#
# Usage:
#   append_event.sh --project <dir> --event <name> \
#     [--field key=value ...]        # string-valued fields (JSON-escaped)
#     [--raw   key=<json> ...]       # raw JSON fields (numbers/bools/null/arrays)
#
# Behavior: reads the max seq already present in <dir>/event-log.jsonl (0 if the
# file is absent/empty), writes seq = max+1. Refuses a non-monotonic log.
# Fail closed: a missing project dir or unwritable log is an error (exit 2).
# Exit: 0 appended, 2 usage/precondition error.

set -uo pipefail

die() { echo "error: $*" >&2; exit 2; }
need_val() { [ "$#" -ge 2 ] || die "$1 needs a value"; case "$2" in -*|"") die "$1 needs a non-option value";; esac; }

PROJECT=""; EVENT=""
FIELD_KEYS=(); FIELD_VALS=(); RAW_KEYS=(); RAW_VALS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --project) need_val "$@"; PROJECT="$2"; shift 2 ;;
    --event) need_val "$@"; EVENT="$2"; shift 2 ;;
    --field) need_val "$@"; FIELD_KEYS+=("${2%%=*}"); FIELD_VALS+=("${2#*=}"); shift 2 ;;
    --raw)   need_val "$@"; RAW_KEYS+=("${2%%=*}"); RAW_VALS+=("${2#*=}"); shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$PROJECT" ] || die "--project is required"
[ -n "$EVENT" ] || die "--event is required"
[ -d "$PROJECT" ] || die "project dir not found: $PROJECT"
LOG="$PROJECT/event-log.jsonl"
[ -e "$LOG" ] || : > "$LOG" || die "cannot create event log: $LOG"
[ -w "$LOG" ] || die "event log not writable: $LOG"

# Serialize read-max + append so concurrent callers cannot mint duplicate seqs.
# mkdir is atomic on POSIX filesystems; clean the lock on any exit.
LOCK="$LOG.lock"
_tries=0
until mkdir "$LOCK" 2>/dev/null; do
  _tries=$((_tries+1)); [ "$_tries" -ge 100 ] && die "event log busy (lock held): $LOCK"
  sleep 0.1
done
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

# Build and append via python3 for correct JSON + strict monotonicity guard.
EVENT="$EVENT" LOG="$LOG" \
FKEYS="$(printf '%s\n' "${FIELD_KEYS[@]:-}")" FVALS="$(printf '%s\n' "${FIELD_VALS[@]:-}")" \
RKEYS="$(printf '%s\n' "${RAW_KEYS[@]:-}")" RVALS="$(printf '%s\n' "${RAW_VALS[@]:-}")" \
python3 - <<'PY' || die "append failed"
import json, os, sys, datetime

log = os.environ["LOG"]
event = os.environ["EVENT"]

def fail(msg):
    print(f"refusing to append: {msg}", file=sys.stderr)
    sys.exit(1)

def pairs(kenv, venv):
    ks = os.environ.get(kenv, "").split("\n")
    vs = os.environ.get(venv, "").split("\n")
    return [(k, v) for k, v in zip(ks, vs) if k != ""]

# Validate the ENTIRE existing log before appending: strictly-increasing int
# seq, each line an object with event + ts. A broken log is not extended.
prev = 0
try:
    with open(log, encoding="utf-8") as fh:
        for i, ln in enumerate(fh, 1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError:
                fail(f"corrupt JSON at line {i}: {ln[:80]}")
            if not isinstance(obj, dict):
                fail(f"line {i} is not an object")
            s = obj.get("seq")
            # bool is a subclass of int in Python; reject it explicitly.
            if type(s) is not int or isinstance(s, bool):
                fail(f"line {i} seq is not an integer: {s!r}")
            if s <= prev:
                fail(f"line {i} seq {s} not strictly increasing (prev {prev})")
            if not (isinstance(obj.get("event"), str) and obj["event"]):
                fail(f"line {i} missing non-empty event")
            if not (isinstance(obj.get("ts"), str) and obj["ts"]):
                fail(f"line {i} missing non-empty ts")
            prev = s
except FileNotFoundError:
    pass

rec = {"ts": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
       "seq": prev + 1, "event": event}
for k, v in pairs("FKEYS", "FVALS"):
    rec[k] = v
for k, v in pairs("RKEYS", "RVALS"):
    try:
        rec[k] = json.loads(v)   # numbers/bools/null/arrays/objects
    except json.JSONDecodeError:
        fail(f"--raw {k}: value is not valid JSON: {v[:60]}")

with open(log, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
print(f"appended seq={rec['seq']} event={event}")
PY
