#!/usr/bin/env bash
# state_check.sh - fail-closed lifecycle/task state-machine gate for the
# project-build-loop conductor. Validates that a proposed phase or task-status
# transition is legal, and that a task marked `done` has closure proof in its
# steps ledger. Run before checkpoint, consult, and publish.
#
# Usage:
#   state_check.sh phase   --from <p> --to <p> [--allow-regress]
#   state_check.sh phase   --project <dir> --to <p> [--allow-regress]
#   state_check.sh task    --project <dir> --task <N.N> --to <s> [--allow-reopen]
#   state_check.sh closure --project <dir> --task <N.N> [--task-json <path>]
#
# Phases (ordered): intake > discovery > classify > roadmap > task-loop >
#   consult > completion. Legal: same, next, or consult->task-loop (loop back).
#   Any other move needs --allow-regress.
# Task status: todo->{in-progress,blocked}; in-progress->{blocked,done};
#   blocked->{in-progress,todo}; done is terminal (reopen needs --allow-reopen).
# Project-aware task transitions derive the current status from project.json and
#   require every depends_on task to be done before in-progress or done.
# Closure: build-log/task-<id>.steps.md must show >=1 real validation/evidence
#   row OR a documented limitation. A transition to done re-runs this gate.
#
# Exit: 0 allow, 1 block, 2 usage.

set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

die() { echo "error: $*" >&2; exit 2; }
block() { echo "BLOCK: $*" >&2; exit 1; }
allow() { echo "ALLOW: $*"; exit 0; }
need_val() { [ "$#" -ge 2 ] || die "$1 needs a value"; case "$2" in -*|"") die "$1 needs a non-option value";; esac; }

[ "$#" -ge 1 ] || die "mode required (phase|task|closure)"
MODE="$1"; shift

FROM=""; TO=""; PROJECT=""; TASK=""; TASK_JSON=""; ALLOW_REGRESS=0; ALLOW_REOPEN=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --from) need_val "$@"; FROM="$2"; shift 2 ;;
    --to) need_val "$@"; TO="$2"; shift 2 ;;
    --project) need_val "$@"; PROJECT="$2"; shift 2 ;;
    --task) need_val "$@"; TASK="$2"; shift 2 ;;
    --task-json) need_val "$@"; TASK_JSON="$2"; shift 2 ;;
    --allow-regress) ALLOW_REGRESS=1; shift ;;
    --allow-reopen) ALLOW_REOPEN=1; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

PHASES="intake discovery classify roadmap task-loop consult completion"
phase_index() { # -> index or -1
  local i=0 p
  for p in $PHASES; do [ "$p" = "$1" ] && { echo "$i"; return; }; i=$((i+1)); done
  echo "-1"
}

case "$MODE" in
  phase)
    if [ -z "$FROM" ] && [ -n "$PROJECT" ]; then
      [ -f "$PROJECT/project.json" ] || die "no project.json in $PROJECT"
      FROM=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("phase",""))' "$PROJECT/project.json" 2>/dev/null)
    fi
    [ -n "$FROM" ] || die "phase mode needs --from or --project"
    [ -n "$TO" ] || die "phase mode needs --to"
    fi_=$(phase_index "$FROM"); ti_=$(phase_index "$TO")
    [ "$fi_" -ge 0 ] || block "unknown from-phase: $FROM"
    [ "$ti_" -ge 0 ] || block "unknown to-phase: $TO"
    # legal: same, advance by one, or consult(5)->task-loop(4)
    if [ "$ti_" -eq "$fi_" ] || [ "$ti_" -eq $((fi_+1)) ] \
       || { [ "$FROM" = "consult" ] && [ "$TO" = "task-loop" ]; }; then
      allow "phase $FROM -> $TO"
    fi
    [ "$ALLOW_REGRESS" -eq 1 ] && allow "phase $FROM -> $TO (regress override)"
    block "illegal phase transition $FROM -> $TO (use --allow-regress with rationale)"
    ;;
  task)
    [ -n "$PROJECT" ] || die "task mode needs --project; raw --from transitions are not a lifecycle gate"
    [ -n "$TASK" ] || die "task mode needs --task"
    [ -n "$TO" ] || die "task mode needs --to"
    [ -f "$PROJECT/project.json" ] || die "no project.json in $PROJECT"
    UNMET=""
    if ! python3 "$SCRIPT_DIR/validate_state.py" project "$PROJECT/project.json" >/dev/null; then
      block "project state or task dependency graph is invalid"
    fi
    TASK_INFO=$(python3 - "$PROJECT/project.json" "$TASK" <<'PY'
import json, sys

project = json.load(open(sys.argv[1], encoding="utf-8"))
task_id = sys.argv[2]
tasks = project.get("tasks", [])
task = next((item for item in tasks if item.get("id") == task_id), None)
if task is None:
    sys.exit(3)
status = {item["id"]: item["status"] for item in tasks}
unmet = [dep for dep in task.get("depends_on", []) if status.get(dep) != "done"]
print(project["schema_version"])
print(task["status"])
print(", ".join(unmet))
PY
    )
    rc=$?
    [ "$rc" -eq 0 ] || block "task $TASK is not present in project.json"
    PROJECT_SCHEMA_VERSION=$(printf '%s\n' "$TASK_INFO" | sed -n '1p')
    [ "$PROJECT_SCHEMA_VERSION" = "1.1" ] \
      || block "project schema $PROJECT_SCHEMA_VERSION must be migrated to 1.1 with explicit depends_on edges before task work"
    DERIVED_FROM=$(printf '%s\n' "$TASK_INFO" | sed -n '2p')
    UNMET=$(printf '%s\n' "$TASK_INFO" | sed -n '3p')
    if [ -n "$FROM" ] && [ "$FROM" != "$DERIVED_FROM" ]; then
      block "task $TASK status mismatch: --from $FROM, project.json $DERIVED_FROM"
    fi
    FROM="$DERIVED_FROM"
    legal=0
    case "$FROM" in
      todo)        case "$TO" in todo|in-progress|blocked) legal=1 ;; esac ;;
      in-progress) case "$TO" in in-progress|blocked|done) legal=1 ;; esac ;;
      blocked)     case "$TO" in blocked|in-progress|todo) legal=1 ;; esac ;;
      done)        case "$TO" in done) legal=1 ;; in-progress) [ "$ALLOW_REOPEN" -eq 1 ] && legal=1 ;; esac ;;
      *) block "unknown from-status: $FROM" ;;
    esac
    case "$TO" in todo|in-progress|blocked|done) : ;; *) block "unknown to-status: $TO" ;; esac
    if [ "$legal" -eq 1 ]; then
      case "$TO" in
        in-progress|done)
          if [ -n "$UNMET" ]; then
            block "task $TASK has unmet dependencies: $UNMET"
          fi
          ;;
      esac
      if [ "$TO" = "done" ]; then
        if [ -n "$TASK_JSON" ]; then
          "$SCRIPT_DIR/state_check.sh" closure --project "$PROJECT" --task "$TASK" --task-json "$TASK_JSON" >/dev/null 2>&1 \
            || block "task $TASK lacks closure proof"
        else
          "$SCRIPT_DIR/state_check.sh" closure --project "$PROJECT" --task "$TASK" >/dev/null 2>&1 \
            || block "task $TASK lacks closure proof"
        fi
      fi
      allow "task $TASK status $FROM -> $TO (dependencies satisfied)"
    fi
    [ "$FROM" = "done" ] && block "task is done (terminal); reopen needs --allow-reopen"
    block "illegal task transition $FROM -> $TO"
    ;;
  closure)
    [ -n "$PROJECT" ] || die "closure mode needs --project"
    [ -n "$TASK" ] || die "closure mode needs --task"
    LEDGER="$PROJECT/build-log/task-$TASK.steps.md"
    [ -f "$LEDGER" ] || block "no steps ledger for task $TASK (expected $LEDGER); a done task needs one"
    LEDGER="$LEDGER" TASK_JSON="$TASK_JSON" python3 - <<'PY'
import os, re, sys, json

ledger = os.environ["LEDGER"]
text = open(ledger, encoding="utf-8").read()

PLACEHOLDER = re.compile(r"<[a-z][a-z /|-]*>", re.I)          # <check>, <command/path>, ...
# Positive allowlist: only these status words count as a passed validation row.
PASS_STATUS = {"observed", "validated", "passed", "pass", "verified",
               "accepted", "complete", "completed", "done", "ok", "confirmed"}
# Words that explicitly must NOT close a task.
NEG_STATUS = {"pending", "todo", "tbd", "n/a", "na", "blocked", "failed",
              "fail", "rejected", "open", "not run", "skipped", "wip", ""}
NEG_LIMIT = {"", "none", "n/a", "na", "tbd", "no limitations", "no limitation",
             "not applicable", "-"}

# Validation section under any of these headings (aliases).
VAL_HEADINGS = {"validation and evidence", "validation & evidence",
                "validation", "evidence", "validation/evidence"}

def section_lines(headings):
    out, grab = [], False
    for ln in text.splitlines():
        st = ln.strip()
        if st.lower().startswith("## "):
            grab = st[3:].strip().lower() in headings
            continue
        if grab:
            out.append(ln)
    return out

def table(lines):
    """Return (header_cells, [data_row_cells]) for the first markdown table."""
    header, rows = None, []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if set(joined) <= set("-: "):        # separator row
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        rows.append(cells)
    return header, rows

def col(header, *names):
    if not header:
        return -1
    for i, h in enumerate(header):
        if any(n in h for n in names):
            return i
    return -1

def cell(cells, idx):
    return cells[idx].strip() if 0 <= idx < len(cells) else ""

# 1) Validation: a data row whose Status cell is an explicit pass word AND whose
#    proof cells (observed + evidence, when those columns exist) are non-placeholder.
header, rows = table(section_lines(VAL_HEADINGS))
si = col(header, "status")
oi = col(header, "observed", "result")
ei = col(header, "evidence", "pointer", "path")
validated = False
for cells in rows:
    status = cell(cells, si).lower()
    if status not in PASS_STATUS:
        continue
    observed = cell(cells, oi)
    evidence = cell(cells, ei)
    # require at least one real proof cell (no template placeholder, non-empty)
    proof = [v for v in (observed, evidence) if v and not PLACEHOLDER.search(v)]
    if (oi < 0 and ei < 0) or proof:
        validated = True
        break

# 2) Documented limitation: task.json checkpoint.limitations[] with real content,
#    or a `## Limitations` section with a real bullet (reject none/n-a/tbd).
limitation = False
tj = os.environ.get("TASK_JSON", "")
if tj and os.path.isfile(tj):
    try:
        obj = json.load(open(tj, encoding="utf-8"))
        lims = obj.get("checkpoint", {}).get("limitations", [])
        if isinstance(lims, list):
            for x in lims:
                s = str(x).strip()
                if s and s.lower() not in NEG_LIMIT and not PLACEHOLDER.search(s):
                    limitation = True
                    break
    except (OSError, json.JSONDecodeError):
        pass
if not limitation:
    for ln in section_lines({"limitations", "limitation"}):
        st = ln.strip()
        if st.startswith(("-", "*")):
            body = st.lstrip("-* ").strip()
            if body and body.lower() not in NEG_LIMIT and not PLACEHOLDER.search(body):
                limitation = True
                break

if validated or limitation:
    print(f"closure proof present (validation={validated}, limitation={limitation})")
    sys.exit(0)
print("no passed validation/evidence row and no documented limitation in steps ledger", file=sys.stderr)
sys.exit(1)
PY
    rc=$?
    [ "$rc" -eq 0 ] && allow "task $TASK closure proof present"
    block "task $TASK lacks closure proof (need a real validation/evidence row or a documented limitation)"
    ;;
  *) die "unknown mode: $MODE (phase|task|closure)" ;;
esac
