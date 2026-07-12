#!/usr/bin/env python3
"""validate_state.py - structural validation for project-build-loop state.

The files in references/schemas/ are shape *examples* (they carry literal union
strings like "todo | in-progress | blocked | done"), not machine JSON Schema.
This validator enforces the documented shape with the standard library only:
required keys, controlled enums, and type sanity. Fail closed.

Usage:
  validate_state.py project <project.json>
  validate_state.py task [--example] <task.json> [<task.json> ...]
  validate_state.py event-log <event-log.jsonl>

--example exempts a union-string reference example (references/schemas/task.json)
from enum checks. Real task files are always validated strictly.

Exit: 0 valid, 1 invalid, 2 usage.
"""
from __future__ import annotations

import json
import sys

PHASES = ["intake", "discovery", "classify", "roadmap", "task-loop", "consult", "completion"]
PROJECT_SCHEMA_VERSIONS = {"1.0", "1.1"}
CLASS_STATUS = {"provisional", "confirmed", "review_required"}
TIERS = {"T0", "T1", "T2", "T3", "T4"}
PUBLISH_POLICY = {"no-publish", "defensive-only", "sanitized-only", "publishable"}
GIT_POLICY = {"local-only", "private-remote", "public-remote"}
TASK_STATUS = {"todo", "in-progress", "blocked", "done"}
TASK_GATE = {
    "authorize", "baseline", "build", "deploy", "execute",
    "validate", "redact", "publish-approval", "decommission",
}


def _load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _enum(errs, label, value, allowed):
    if not isinstance(value, str) or value not in allowed:
        errs.append(f"{label}: {value!r} not in {sorted(allowed)}")


def _depends_on(errs, label: str, task_id, value) -> list[str]:
    """Validate one dependency list and return its usable string IDs."""
    if value is None:
        errs.append(f"{label}: must be an array of task IDs")
        return []
    if not isinstance(value, list):
        errs.append(f"{label}: must be an array of task IDs")
        return []
    deps: list[str] = []
    seen: set[str] = set()
    for i, dep in enumerate(value):
        item_label = f"{label}[{i}]"
        if not isinstance(dep, str) or not dep.strip():
            errs.append(f"{item_label}: must be a non-empty string")
            continue
        if dep != dep.strip():
            errs.append(f"{item_label}: task ID must not have surrounding whitespace")
            continue
        if dep in seen:
            errs.append(f"{item_label}: duplicate dependency {dep!r}")
            continue
        if isinstance(task_id, str) and dep == task_id:
            errs.append(f"{item_label}: task cannot depend on itself")
            continue
        seen.add(dep)
        deps.append(dep)
    return deps


def _validate_project_tasks(errs, tasks, require_explicit_dependencies: bool) -> None:
    """Validate task summaries and their dependency graph, fail closed."""
    if not isinstance(tasks, list):
        errs.append("tasks: must be an array")
        return

    task_ids: set[str] = set()
    graph: dict[str, list[str]] = {}
    for i, task in enumerate(tasks):
        label = f"tasks[{i}]"
        if not isinstance(task, dict):
            errs.append(f"{label}: must be an object")
            continue
        for key in ("id", "title", "status"):
            if key not in task:
                errs.append(f"{label}.{key}: missing")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            errs.append(f"{label}.id: must be a non-empty string")
            continue
        if task_id != task_id.strip():
            errs.append(f"{label}.id: task ID must not have surrounding whitespace")
            continue
        if task_id in task_ids:
            errs.append(f"{label}.id: duplicate task ID {task_id!r}")
            continue
        task_ids.add(task_id)
        if "status" in task:
            _enum(errs, f"{label}.status", task["status"], TASK_STATUS)
        if require_explicit_dependencies and "depends_on" not in task:
            errs.append(f"{label}.depends_on: missing in project schema 1.1")
        graph[task_id] = _depends_on(
            errs, f"{label}.depends_on", task_id, task.get("depends_on", [])
        )

    for task_id, deps in graph.items():
        for dep in deps:
            if dep not in task_ids:
                errs.append(
                    f"task {task_id!r}: dependency {dep!r} does not reference a project task"
                )

    # DFS over task -> dependency edges. Unknown edges were reported above and
    # are skipped here so the cycle diagnostic remains deterministic.
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(task_id: str) -> list[str] | None:
        state[task_id] = 1
        stack.append(task_id)
        for dep in graph.get(task_id, []):
            if dep not in graph:
                continue
            if state.get(dep, 0) == 0:
                cycle = visit(dep)
                if cycle:
                    return cycle
            elif state.get(dep) == 1:
                start = stack.index(dep)
                return stack[start:] + [dep]
        stack.pop()
        state[task_id] = 2
        return None

    for task_id in graph:
        if state.get(task_id, 0) == 0:
            cycle = visit(task_id)
            if cycle:
                errs.append(f"tasks: dependency cycle detected: {' -> '.join(cycle)}")
                break


def validate_project(path: str) -> list[str]:
    errs: list[str] = []
    try:
        p = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read/parse {path}: {exc}"]
    if not isinstance(p, dict):
        return [f"{path}: top level is not an object"]
    for key in ("schema_version", "id", "title", "category", "phase", "classification"):
        if key not in p:
            errs.append(f"missing required key: {key}")
    schema_version = p.get("schema_version")
    if "schema_version" in p:
        _enum(errs, "schema_version", schema_version, PROJECT_SCHEMA_VERSIONS)
    if "phase" in p:
        _enum(errs, "phase", p["phase"], set(PHASES))
    cls = p.get("classification")
    if not isinstance(cls, dict):
        errs.append("classification: missing or not an object")
    else:
        for key in ("status", "dual_use_tier", "publish_policy", "git_policy"):
            if key not in cls:
                errs.append(f"classification.{key}: missing")
        if "status" in cls:
            _enum(errs, "classification.status", cls["status"], CLASS_STATUS)
        if "dual_use_tier" in cls:
            _enum(errs, "classification.dual_use_tier", cls["dual_use_tier"], TIERS)
        if "publish_policy" in cls:
            _enum(errs, "classification.publish_policy", cls["publish_policy"], PUBLISH_POLICY)
        if "git_policy" in cls:
            _enum(errs, "classification.git_policy", cls["git_policy"], GIT_POLICY)
    if "tasks" in p:
        _validate_project_tasks(
            errs,
            p["tasks"],
            require_explicit_dependencies=schema_version == "1.1",
        )
    return errs


def validate_task(path: str, allow_example: bool = False) -> list[str]:
    errs: list[str] = []
    try:
        t = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read/parse {path}: {exc}"]
    if not isinstance(t, dict):
        return [f"{path}: top level is not an object"]
    for key in ("id", "title", "status", "gate"):
        if key not in t:
            errs.append(f"missing required key: {key}")
    # The shipped reference example carries union-string values as documentation
    # ("todo | in-progress | ..."). Only skip enum checks when the caller opts in
    # via --example; a real task file is always validated strictly.
    is_example = allow_example and "|" in str(t.get("status", ""))
    if not is_example:
        _enum(errs, "status", t.get("status"), TASK_STATUS)
        _enum(errs, "gate", t.get("gate"), TASK_GATE)
    return errs


def validate_event_log(path: str) -> list[str]:
    errs: list[str] = []
    try:
        with open(path, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]
    prev = 0
    for i, ln in enumerate(lines, 1):
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as exc:
            errs.append(f"line {i}: invalid JSON: {exc}")
            continue
        if "seq" not in obj or "event" not in obj or "ts" not in obj:
            errs.append(f"line {i}: missing seq/event/ts")
            continue
        if not (isinstance(obj["event"], str) and obj["event"]):
            errs.append(f"line {i}: event is not a non-empty string")
        if not (isinstance(obj["ts"], str) and obj["ts"]):
            errs.append(f"line {i}: ts is not a non-empty string")
        seq = obj["seq"]
        # bool is a subclass of int; reject True/False as a sequence number.
        if type(seq) is not int or isinstance(seq, bool):
            errs.append(f"line {i}: seq {seq!r} is not an integer")
        elif seq <= prev:
            errs.append(f"line {i}: seq {seq} not strictly increasing (prev {prev})")
        else:
            prev = seq
    return errs


def main(argv: list[str]) -> int:
    args = argv[1:]
    allow_example = False
    if "--example" in args:
        allow_example = True
        args = [a for a in args if a != "--example"]
    if len(args) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    kind, paths = args[0], args[1:]
    if kind not in ("project", "task", "event-log"):
        print(f"unknown kind: {kind} (project|task|event-log)", file=sys.stderr)
        return 2
    all_errs: list[str] = []
    for path in paths:
        if kind == "task":
            errs = validate_task(path, allow_example=allow_example)
        elif kind == "project":
            errs = validate_project(path)
        else:
            errs = validate_event_log(path)
        all_errs.extend(f"{path}: {e}" for e in errs)
    if all_errs:
        print("INVALID:", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"valid: {' '.join(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
