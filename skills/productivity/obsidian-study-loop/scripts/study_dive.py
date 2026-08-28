#!/usr/bin/env python3
"""Scaffold and check deep-dive handoffs for the active study-loop session.

Scaffold mode collects needs-remediation objectives from the active version 2
session and writes a dive handoff under _study/dives/ containing the routed gap
topics, the teaching flow, and the writing chain (technical-writing draft,
unslop pass, humanizer final rewrite, portable-markdown lint).

Check mode verifies a handoff whose writing chain is complete. Neither mode
writes to Notes/, the session ledger, or state.json.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

from validate_study_vault import (
    frontmatter,
    frontmatter_value,
    parse_objective_status_rows,
)

CHECK_BOX = "- [ ] "
DONE_BOX = "- [x] "
CHAIN_STEPS = (
    "technical-writing",
    "unslop",
    "humanizer",
    "portable-markdown",
)


def fail(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def local_now() -> str:
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def slug(text: str) -> str:
    slugged = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slugged or "dive"


def section(raw: str, title: str) -> str:
    match = re.search(
        rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)",
        raw,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        fail(f"session has no '## {title}' section")
    return match.group(1)


def load_active_session(vault: Path) -> tuple[Path, dict, list[dict]]:
    state_path = vault / "_study" / "state.json"
    if not state_path.exists():
        fail(f"no _study/state.json under {vault}")
    try:
        state = json.loads(state_path.read_text())
        session_rel = state["active_session"]
    except (json.JSONDecodeError, KeyError) as exc:
        fail(f"malformed state.json: {exc}")
    session_path = vault / session_rel
    if not session_path.exists():
        fail(f"active session not found: {session_rel}")
    meta = frontmatter(session_path.read_text())
    if frontmatter_value(meta, "study-loop-version") != "2":
        fail(f"{session_rel} is not a version 2 session; legacy dives do not use handoffs")
    return session_path, meta, [session_path, vault]


def gap_rows(session_path: Path) -> list[dict]:
    raw = session_path.read_text()
    try:
        rows = parse_objective_status_rows(section(raw, "Objective status"))
    except ValueError as exc:
        fail(str(exc))
    gaps = []
    for objective, note, _content, _drill, competency, reason, _next in rows:
        if competency == "needs-remediation":
            gaps.append({"objective": objective, "note": note, "reason": reason})
    return gaps


def build_handoff(
    scope: str,
    session_rel: str,
    gaps: list[dict],
    extras: list[str],
) -> str:
    now = local_now()
    topic_lines = []
    for gap in gaps:
        topic_lines.append(f"- {gap['objective']} — {gap['reason']}\n  - Source: {gap['note']}")
    for extra in extras:
        topic_lines.append(f"- {extra} — learner-requested topic\n  - Source: resolve against the session scope")
    topics = "\n".join(topic_lines)
    return f"""---
type: dive-handoff
scope: {scope}
created: {now}
session: {session_rel}
---

# Dive handoff — {scope}

> [!NOTE]
> **Dive handoff — not an assessment.** Teaching material only. The dive never
> changes mastery, never writes `Notes/`, and never collects scored answers.

## Gap topics

{topics}

## Teaching flow

1. Relevance-resolve every topic against the session (in-scope, adjacent,
   unrelated) per Mid-Session Deep Dives before teaching it.
2. Run the real helper: `teach-complex-concepts` for conceptual gaps,
   `evidence-research-loop` when the defect sits in the source content rather
   than the learner.
3. Teaching rhythm: orient, focused chunk, worked example, learner retrieval,
   corrective feedback, teach-back. Keep chunks small.

## Writing chain

Complete in order. The dive is saved only when every box is ticked and
`--check` passes.

{CHECK_BOX}1. technical-writing — choose one Diátaxis mode (explanation or how-to), one thought per sentence, no ambiguous instructions.
{CHECK_BOX}2. unslop — preservation-first pass: technical terms, exact commands, citations, and the neutral technical register survive unchanged.
{CHECK_BOX}3. humanizer — draft-audit-final rewrite of the finished prose; persist only the final rewrite.
{CHECK_BOX}4. portable-markdown — `lint.sh` clean: no `%%` comments, standard alert types only.

## Boundaries

- Teaching answers are learning activity, never mastery evidence.
- No learner answers, mistakes, or scores are stored in this file.
- The fresh transfer check after the dive runs through the normal assess path
  on a new surface.

## Session record (paste into the session when the dive completes)

```markdown
## Deep dive — {scope}

- <ISO datetime> — <helper skill> — <topic>
  - Trigger: needs-remediation routing after publication
  - Outcome: <what now clicks / what stays fragile — tutor observation only>
  - Persisted: `_study/dives/<YYYY-MM-DD>-<topic-slug>.md`
  - Mastery: unchanged — re-quiz <offered|accepted|declined>, study-check <embedded|none>
```
"""


def scaffold(vault: Path, extras: list[str]) -> None:
    session_path, meta, _ = load_active_session(vault)
    scope = frontmatter_value(meta, "topic")
    if not scope:
        fail("active session has no topic in frontmatter")
    gaps = gap_rows(session_path)
    if not gaps and not extras:
        fail(
            "no needs-remediation objectives in the active session; pass "
            "--objective to hand off a specific topic"
        )
    dives = vault / "_study" / "dives"
    dives.mkdir(parents=True, exist_ok=True)
    target = dives / f"{datetime.date.today().isoformat()}-{slug(scope)}-handoff.md"
    target.write_text(build_handoff(scope, session_path.relative_to(vault).as_posix(), gaps, extras))
    count = len(gaps) + len(extras)
    print(f"Wrote {target} with {count} gap topic(s).")


def check(vault: Path, handoff: Path) -> None:
    if not handoff.exists():
        fail(f"handoff not found: {handoff}", code=1)
    text = handoff.read_text()
    findings: list[str] = []
    if not frontmatter(text):
        findings.append("missing frontmatter")
    unchecked = [line for line in text.splitlines() if line.startswith(CHECK_BOX)]
    if unchecked:
        findings.append(f"{len(unchecked)} writing-chain step(s) unticked")
    for step in CHAIN_STEPS:
        if step not in text:
            findings.append(f"writing chain is missing its {step} step")
    if "## Gap topics" not in text:
        findings.append("missing Gap topics section")
    if "%%" in re.sub(r"`[^`]*`", "", text):
        findings.append("Obsidian-only %% syntax present")
    if re.search(r"\bWrite here\b", text):
        findings.append("learner placeholder text present")
    if findings:
        for finding in findings:
            print(f"FINDING: {finding}")
        sys.exit(1)
    print(f"OK: {handoff.name} — chain complete, portable, no placeholders.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path, help="Obsidian vault path")
    parser.add_argument(
        "--objective",
        action="append",
        default=[],
        help="explicit gap topic to hand off (repeatable)",
    )
    parser.add_argument(
        "--check",
        type=Path,
        help="verify a completed handoff instead of scaffolding",
    )
    args = parser.parse_args()
    vault = args.vault.resolve()
    if not vault.exists():
        fail(f"vault path does not exist: {vault}")
    if args.check:
        check(vault, args.check if args.check.is_absolute() else vault / args.check)
    else:
        scaffold(vault, args.objective)


if __name__ == "__main__":
    main()
