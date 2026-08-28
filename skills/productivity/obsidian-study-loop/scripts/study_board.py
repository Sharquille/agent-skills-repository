#!/usr/bin/env python3
"""Render the active study-loop chapter board without modifying the vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from validate_study_vault import (
    COMPETENCY_STATES,
    CONTENT_STATES,
    DRILL_STATES,
    frontmatter,
    frontmatter_value,
    parse_objective_status_rows,
)


class BoardError(RuntimeError):
    """A user-facing board rendering failure."""


@dataclass(frozen=True)
class Row:
    objective: str
    note: str
    content: str
    drill: str
    competency: str
    reason: str
    next_action: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault_path", nargs="?", default=".")
    parser.add_argument("--session", type=Path)
    return parser.parse_args()


def resolve_session(vault: Path, requested: Path | None) -> Path:
    sessions = (vault / "_study" / "sessions").resolve()
    if requested is not None:
        candidate = requested.expanduser()
        if not candidate.is_absolute():
            candidate = vault / candidate
    else:
        state_path = vault / "_study" / "state.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BoardError(f"cannot read _study/state.json: {exc}") from exc
        if not isinstance(state, dict) or set(state) != {"active_session"}:
            raise BoardError("state.json must contain exactly active_session")
        active = state["active_session"]
        if active is None:
            candidates = sorted(sessions.glob("*.md")) if sessions.is_dir() else []
            if not candidates:
                raise BoardError("there is no active or previous study session")
            candidate = candidates[-1]
        elif isinstance(active, str) and active:
            relative = PurePosixPath(active)
            if relative.is_absolute() or ".." in relative.parts:
                raise BoardError("active_session is not a safe vault-relative path")
            candidate = vault.joinpath(*relative.parts)
        else:
            raise BoardError("active_session must be a string or null")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(sessions) or resolved.suffix != ".md":
        raise BoardError("session must be a Markdown file under _study/sessions")
    if not resolved.is_file():
        raise BoardError(f"session does not exist: {resolved}")
    return resolved


def parse_table(text: str) -> list[Row]:
    match = re.search(
        r"^## Objective status\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise BoardError("session has no ## Objective status table")
    try:
        values_list = parse_objective_status_rows(match.group("body"))
    except ValueError as exc:
        raise BoardError(str(exc)) from exc
    rows: list[Row] = []
    seen: set[str] = set()
    for values in values_list:
        row = Row(*values)
        if row.objective in seen:
            raise BoardError(f"duplicate objective row: {row.objective}")
        seen.add(row.objective)
        if row.content not in CONTENT_STATES:
            raise BoardError(
                f"{row.objective} has unsupported content state: {row.content}"
            )
        if row.drill not in DRILL_STATES:
            raise BoardError(
                f"{row.objective} has unsupported drill state: {row.drill}"
            )
        if row.competency not in COMPETENCY_STATES:
            raise BoardError(
                f"{row.objective} has unsupported competency state: {row.competency}"
            )
        rows.append(row)
    return rows


def render(session: Path, text: str, rows: list[Row]) -> str:
    block = frontmatter(text)
    topic = frontmatter_value(block, "topic") or session.stem
    phase = frontmatter_value(block, "status") or "unknown"
    output = [
        f"# {topic} — review board",
        "",
        f"Phase: **{phase}**",
        "",
        "| Objective | Read | Content | Anki | Competency | Next action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        output.append(
            f"| {row.objective} | {row.note} | {row.content} | {row.drill} | {row.competency} | {row.next_action} |"
        )
    actionable = [
        row for row in rows if row.next_action.lower() not in {"none", "complete"}
    ]
    output.extend(("", "## Now"))
    if actionable:
        first = actionable[0]
        output.append(f"{first.objective}: {first.next_action}")
        if first.reason.lower() not in {"none", "ready"}:
            output.append(f"Reason: {first.reason}")
    else:
        output.append("Chapter complete. Continue Anki reviews independently.")
    return "\n".join(output) + "\n"


def main() -> int:
    args = parse_args()
    try:
        vault = Path(args.vault_path).expanduser().resolve()
        if not vault.is_dir():
            raise BoardError(f"vault is not a directory: {vault}")
        session = resolve_session(vault, args.session)
        text = session.read_text(encoding="utf-8")
        if frontmatter_value(frontmatter(text), "study-loop-version") != "2":
            raise BoardError("the review board requires a version 2 study session")
        sys.stdout.write(render(session, text, parse_table(text)))
    except (BoardError, OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
