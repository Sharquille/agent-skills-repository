#!/usr/bin/env python3
"""Scaffold one Chapter-NN/<section>/ folder in the collecting state.

Writes only the contract boilerplate (state.json, ledger.md source table,
practice-plan.md header). It never writes maps, notes, or Practice.md, and it
refuses to touch an existing section.
"""
import argparse
import json
import re
from pathlib import Path

LEDGER = """# {section} ledger

| ID | Original location | Locator | Extraction | Coverage / availability |
| --- | --- | --- | --- | --- |

## Earned

## Uncertain

## Not earned
"""

PLAN = """# {section} Practice coverage plan

Fill the table from the ledger and Core notes, then state the count as
`Q_min = A + H = <A> + <H> = <total>`.

| Outcome | Core/source anchor | Learner decision | Extra reason | Primary | Varied extra |
| --- | --- | --- | --- | --- | --- |
"""


def scaffold(kit: Path, section: str, week: int, title: str) -> Path:
    if not re.fullmatch(r"\d+(\.\d+)+", section):
        raise ValueError("section must look like 3.2")
    if week < 1:
        raise ValueError("week must be a positive integer from the course calendar")
    if not title.strip():
        raise ValueError("title must be a short human section name")
    if not kit.is_dir():
        raise ValueError(f"{kit} is not a Chapter-Kits folder")
    chapter = kit / f"Chapter-{int(section.split('.')[0]):02d}"
    folder = chapter / section
    if folder.exists():
        raise ValueError(f"{folder} already exists; edit it instead of scaffolding")
    folder.mkdir(parents=True)
    state = {
        "status": "collecting",
        "week": week,
        "title": title.strip(),
        "coverage": "partial",
        "batch": 1,
        "release_note": "",
        "missing": [],
        "verification": {"local": "pending", "http": "pending", "import": "pending"},
    }
    (folder / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    (folder / "ledger.md").write_text(LEDGER.format(section=section))
    (folder / "practice-plan.md").write_text(PLAN.format(section=section))
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--section", required=True, help="e.g. 3.2")
    parser.add_argument("--week", type=int, required=True,
                        help="term week from the course calendar; never inferred from the chapter")
    parser.add_argument("--title", required=True, help="e.g. 'Measures of Variation'")
    args = parser.parse_args()
    try:
        folder = scaffold(args.kit.expanduser().resolve(), args.section, args.week, args.title)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Scaffold stopped: {error}\n")
    print(f"Created {folder} (collecting). Register sources in ledger.md before authoring.")


if __name__ == "__main__":
    main()
