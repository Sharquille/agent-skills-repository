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
    if value not in allowed:
        errs.append(f"{label}: {value!r} not in {sorted(allowed)}")


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
    if "tasks" in p and not isinstance(p["tasks"], list):
        errs.append("tasks: must be an array")
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
