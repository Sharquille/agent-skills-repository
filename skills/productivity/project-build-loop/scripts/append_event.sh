#!/usr/bin/env bash
# append_event.sh - append one JSON event to a project's event-log.jsonl with a
# correct monotonically-increasing seq. Single source of truth for event writes
# (used directly and by the gate-receipt paths in policy_check.sh/secret_scan.sh).
#
# Usage:
#   append_event.sh --project <dir> --event <name> \
#     [--field key=value ...]        # string-valued fields (JSON-escaped)
#     [--raw   key=<json> ...]       # raw JSON fields (numbers/bools/null/arrays)
# Keys must match [A-Za-z_][A-Za-z0-9_]*. The generated ts, seq, and event
# fields are reserved and cannot be supplied through --field or --raw.
#
# Behavior: reads the max seq already present in <dir>/event-log.jsonl (0 if the
# file is absent/empty), writes seq = max+1. Refuses a non-monotonic log.
# Fail closed: a missing project dir or unwritable log is an error (exit 2).
# Exit: 0 appended, 2 usage/precondition error.

set -uo pipefail

die() { echo "error: $*" >&2; exit 2; }
need_val() { [ "$#" -ge 2 ] || die "$1 needs a value"; case "$2" in -*|"") die "$1 needs a non-option value";; esac; }

PROJECT=""; EVENT=""
# A non-empty sentinel keeps expansion safe under Bash 3.2 with `set -u`.
PY_ARGS=(--)

while [ "$#" -gt 0 ]; do
  case "$1" in
    --project) need_val "$@"; PROJECT="$2"; shift 2 ;;
    --event) need_val "$@"; EVENT="$2"; shift 2 ;;
    --field) need_val "$@"; PY_ARGS+=(--field "$2"); shift 2 ;;
    --raw)   need_val "$@"; PY_ARGS+=(--raw "$2"); shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$PROJECT" ] || die "--project is required"
[ -n "$EVENT" ] || die "--event is required"
[ -d "$PROJECT" ] || die "project dir not found: $PROJECT"
LOG="$PROJECT/event-log.jsonl"

# Build and append via python3 for correct JSON, an automatically released
# POSIX advisory lock, strict monotonicity, and a durable successful write.
# Each assignment is passed as its own argv element, preserving all characters
# except NUL (which shell arguments cannot represent), including newlines.
python3 - "$LOG" "$EVENT" "${PY_ARGS[@]}" <<'PY' || die "append failed"
import datetime
import fcntl
import json
import os
import re
import stat
import sys
import time

log = sys.argv[1]
event = sys.argv[2]

def fail(msg):
    print(f"refusing to append: {msg}", file=sys.stderr)
    sys.exit(1)

class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains an ambiguous duplicate key."""

def reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f"duplicate key: {key}")
        obj[key] = value
    return obj

key_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
reserved = {"ts", "seq", "event"}
seen = set()
fields = []
raw_fields = []

args = sys.argv[3:]
if not args or args[0] != "--":
    fail("internal argument transport error")
args = args[1:]
if len(args) % 2:
    fail("internal argument transport error")
for i in range(0, len(args), 2):
    kind, assignment = args[i:i + 2]
    if kind not in ("--field", "--raw"):
        fail(f"internal argument transport error: {kind}")
    key, sep, value = assignment.partition("=")
    if not sep:
        fail(f"{kind} requires key=value")
    if not key_re.fullmatch(key):
        fail(f"{kind} key is invalid: {key!r}")
    if key in reserved:
        fail(f"{kind} cannot set reserved field: {key}")
    if key in seen:
        fail(f"duplicate field: {key}")
    seen.add(key)
    if kind == "--field":
        fields.append((key, value))
    else:
        try:
            raw_fields.append((key, json.loads(value)))
        except json.JSONDecodeError:
            fail(f"--raw {key}: value is not valid JSON: {value[:60]}")

# Serialize full-log validation + append so concurrent callers cannot mint
# duplicate seqs. flock ownership is released by the OS when this process dies,
# including after SIGKILL; the persistent lock file itself carries no state.
project_path = os.path.dirname(log)
project_fd = None
project_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
project_flags |= getattr(os, "O_CLOEXEC", 0)
project_flags |= getattr(os, "O_NOFOLLOW", 0)
try:
    project_fd = os.open(project_path, project_flags)
    if not stat.S_ISDIR(os.fstat(project_fd).st_mode):
        fail(f"project path is not a directory: {project_path}")
except OSError as exc:
    fail(f"cannot open project directory without following symlinks: {exc}")

state_dir = os.path.join(project_path, ".project")
try:
    os.mkdir(".project", 0o700, dir_fd=project_fd)
except FileExistsError:
    pass
except OSError as exc:
    fail(f"cannot create local state directory {state_dir}: {exc}")

# Open the directory without following a symlink, make its existing permissions
# private, then create the lock relative to that verified directory descriptor.
state_fd = None
lock_fd = None
lock_path = os.path.join(state_dir, "event-log.lock")
try:
    state_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    state_flags |= getattr(os, "O_NOFOLLOW", 0)
    state_fd = os.open(".project", state_flags, dir_fd=project_fd)
    if not stat.S_ISDIR(os.fstat(state_fd).st_mode):
        fail(f"local state path is not a directory: {state_dir}")
    os.fchmod(state_fd, 0o700)

    lock_flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
    lock_flags |= getattr(os, "O_CLOEXEC", 0)
    lock_flags |= getattr(os, "O_NOFOLLOW", 0)
    lock_fd = os.open("event-log.lock", lock_flags, 0o600, dir_fd=state_fd)
    os.fchmod(lock_fd, 0o600)
    lock_fh = os.fdopen(lock_fd, "a", encoding="utf-8")
    lock_fd = None  # ownership transferred to lock_fh
except OSError as exc:
    fail(f"cannot open event-log lock {lock_path}: {exc}")
finally:
    if lock_fd is not None:
        os.close(lock_fd)
    if state_fd is not None:
        os.close(state_fd)

with lock_fh:
    deadline = time.monotonic() + 10.0
    while True:
        try:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fail(f"event log busy (lock held): {lock_path}")
            time.sleep(0.1)
        except OSError as exc:
            fail(f"cannot lock event log {lock_path}: {exc}")

    # Open/create the log exactly once, relative to the verified project
    # directory. O_NOFOLLOW rejects a symlink at the event-log path; validation
    # and append both use this same descriptor so the pathname cannot be swapped
    # between the two operations.
    log_fd = None
    try:
        log_flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
        log_flags |= getattr(os, "O_CLOEXEC", 0)
        log_flags |= getattr(os, "O_NOFOLLOW", 0)
        log_fd = os.open("event-log.jsonl", log_flags, 0o666, dir_fd=project_fd)
        if not stat.S_ISREG(os.fstat(log_fd).st_mode):
            fail(f"event log is not a regular file: {log}")
        log_fh = os.fdopen(log_fd, "r+b", buffering=0)
        log_fd = None  # ownership transferred to log_fh
    except OSError as exc:
        fail(f"cannot open event log without following symlinks {log}: {exc}")
    finally:
        if log_fd is not None:
            os.close(log_fd)

    # Validate the ENTIRE existing log while holding the append lock. A broken
    # log is never extended: seq must be a strictly increasing non-bool int,
    # and every record must contain a non-empty event and timestamp.
    prev = 0
    try:
        with log_fh:
            log_fh.seek(0)
            for line_no, raw_line in enumerate(log_fh, 1):
                try:
                    line = raw_line.decode("utf-8").strip()
                except UnicodeDecodeError as exc:
                    fail(f"event log is not UTF-8 at line {line_no}: {exc}")
                if not line:
                    continue
                try:
                    obj = json.loads(line, object_pairs_hook=reject_duplicate_keys)
                except DuplicateKeyError as exc:
                    fail(f"duplicate JSON object key at line {line_no}: {exc}")
                except json.JSONDecodeError:
                    fail(f"corrupt JSON at line {line_no}: {line[:80]}")
                if not isinstance(obj, dict):
                    fail(f"line {line_no} is not an object")
                seq = obj.get("seq")
                # bool is a subclass of int in Python; require the exact type.
                if type(seq) is not int:
                    fail(f"line {line_no} seq is not an integer: {seq!r}")
                if seq <= prev:
                    fail(
                        f"line {line_no} seq {seq} not strictly increasing "
                        f"(prev {prev})"
                    )
                if not (isinstance(obj.get("event"), str) and obj["event"]):
                    fail(f"line {line_no} missing non-empty event")
                if not (isinstance(obj.get("ts"), str) and obj["ts"]):
                    fail(f"line {line_no} missing non-empty ts")
                prev = seq

            rec = {
                "ts": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
                "seq": prev + 1,
                "event": event,
            }
            rec.update(fields)
            rec.update(raw_fields)
            payload = (json.dumps(rec, separators=(",", ":")) + "\n").encode(
                "utf-8"
            )
            remaining = memoryview(payload)
            while remaining:
                written = log_fh.write(remaining)
                if not written:
                    fail(f"short write appending event log {log}")
                remaining = remaining[written:]
            log_fh.flush()
            os.fsync(log_fh.fileno())
    except OSError as exc:
        fail(f"cannot validate or append event log {log}: {exc}")

os.close(project_fd)

print(f"appended seq={rec['seq']} event={event}")
PY
