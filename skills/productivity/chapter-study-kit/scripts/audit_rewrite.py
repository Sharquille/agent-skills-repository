#!/usr/bin/env python3
"""Compare a rewritten section with its snapshot from before the rewrite.

Run it after any rewrite, especially one another model wrote. It checks what a
rewrite must keep (heading numbers, figures, Practice items, Review pointers that
land on a heading) and reports the word change, so cuts that never happened, or
cuts that went too far, show up before the Sol review. Stdlib only.

    python3 audit_rewrite.py --before <snapshot>/Chapter-05/5.1 --after <kit>/Chapter-05/5.1
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORE_STOP = re.compile(r"(?im)^#\s+.*\b(?:quiz why|retrieval)\s*$")
HEADING = re.compile(r"(?m)^### (\d+[a-z]?)\.")
FIGURE = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
QUESTION = re.compile(r"\[!question\]-")
REVIEW = re.compile(r"\*\*Review:\*\*\s*([^\n]*)")
CORE_REF = re.compile(r"Core (\d+[a-z]?)")
# A rewrite that cuts less than this share of the words probably skipped the repetition pass.
MIN_CUT = 0.05


def notes(folder: Path) -> Path:
    found = sorted(folder.glob("*Study-Notes.md"))
    if len(found) != 1:
        raise SystemExit(f"{folder}: need exactly one *Study-Notes.md")
    return found[0]


def core(path: Path) -> str:
    return CORE_STOP.split(path.read_text())[0]


def audit(before: Path, after: Path) -> tuple[list[str], list[str]]:
    """Return (problems, facts). Problems are things the rewrite lost or broke."""
    problems, facts = [], []
    old, new = core(notes(before)), core(notes(after))
    old_heads, new_heads = HEADING.findall(old), HEADING.findall(new)
    if old_heads != new_heads:
        problems.append(f"heading numbers changed: {old_heads} -> {new_heads}")
    lost_figures = sorted(set(FIGURE.findall(old)) - set(FIGURE.findall(new)))
    if lost_figures:
        problems.append(f"figures dropped from Core: {', '.join(lost_figures)}")
    old_q = len(QUESTION.findall((before / "Practice.md").read_text())) if (before / "Practice.md").is_file() else 0
    practice = (after / "Practice.md").read_text() if (after / "Practice.md").is_file() else ""
    new_q = len(QUESTION.findall(practice))
    if new_q < old_q:
        problems.append(f"Practice items fell from {old_q} to {new_q}")
    stray = sorted({ref for pointer in REVIEW.findall(practice) for ref in CORE_REF.findall(pointer)}
                   - set(new_heads), key=lambda r: (len(r), r))
    if stray:
        problems.append(f"Review pointers name missing headings: Core {', '.join(stray)}")
    old_words, new_words = len(old.split()), len(new.split())
    change = (old_words - new_words) / old_words if old_words else 0.0
    facts.append(f"words {old_words} -> {new_words} ({change:.0%} cut)")
    if change < MIN_CUT:
        problems.append(f"Core cut only {change:.0%}; check that repeats and Tier 3 detail were removed")
    ledger = (after / "ledger.md").read_text() if (after / "ledger.md").is_file() else ""
    for section in ("## Relevance", "## Context"):
        if section not in ledger:
            problems.append(f"ledger.md has no {section[3:]} section")
    return problems, facts


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare a rewritten section with its snapshot.")
    ap.add_argument("--before", required=True, type=Path, help="snapshot of the section folder before the rewrite")
    ap.add_argument("--after", required=True, type=Path, help="the rewritten section folder")
    args = ap.parse_args()
    problems, facts = audit(args.before, args.after)
    for fact in facts:
        print(fact)
    for problem in problems:
        print(f"problem: {problem}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
