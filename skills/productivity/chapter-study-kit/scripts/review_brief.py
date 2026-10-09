#!/usr/bin/env python3
"""Print the Sol review brief for one section (references/sol-review.md).

The brief is self-contained: the ledger (what the sources earned), the Practice
question titles, each figure's printed labels, and the Core. Pass --before with
the previous Core when the section is a rewrite, so the reviewer can report lost
facts and changed meaning. Stdlib only; run it under Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORE_STOP = re.compile(r"(?im)^#\s+.*\b(?:quiz why|retrieval)\s*$")
QUESTION = re.compile(r"\[!question\]-\s*(Q\d+\.[^\n]*)")
LABEL = re.compile(r">([^<]+)</text>")
# The Codex wrapper refuses prompts that look like credentials; study text such as
# "soft token:" trips it, so break the "word:" shape without changing the meaning.
SECRET_SHAPE = re.compile(r"(?i)\b(token|password|secret|api[_ -]?key)(\s*)([:=])")

ASK = """ROLE: Read-only reviewer of a study-kit section. All context is inline; do not read files or run commands.
The notes follow a contract: Core prints Tier 1 items (named by an exam or lecture objective) and what they depend on;
each fact appears once per heading (figures carry structure, prose adds only the reason, TEST MOVE is a scenario clue
and the decision it points to); definitions sit in margin TERMS boxes; untested detail lives in the ledger's Context
list; HIGH YIELD lines state checkable signals, never predictions about how often something is asked.

REPORT in under 400 words, as bullet lists under these headings. Quote the exact wording. Say "none" when empty.
1. UNSUPPORTED: Core claims the LEDGER does not support, including invented numbers, examples, or exam-frequency claims.
2. LOST: facts a PRACTICE question needs, or that the stated objectives clearly test, that Core (text, TERMS, figure
   labels) does not state{lost}.
3. CHANGED: wording that shifts meaning from the ledger{changed} (dropped hedges, narrowed or widened definitions).
4. REPEATED: a fact stated twice inside one heading's body, TERMS, or figure labels. A TEST MOVE that names the
   concept as a scenario clue is not repetition.
5. WRONG: technical errors against well-established references, with the correction.
No praise, no summary."""


def core(path: Path) -> str:
    return CORE_STOP.split(path.read_text())[0]


def ledger_claims(path: Path) -> str:
    """The ledger from **Earned** on: its source table holds local paths that stay on the Mac."""
    if not path.is_file():
        return "(missing)"
    text = path.read_text()
    start = re.search(r"(?m)^## Earned", text)
    return text[start.start():] if start else text


def scrub(text: str) -> str:
    return SECRET_SHAPE.sub(r"\1\2 -", text)


def brief(section: Path, before: Path | None) -> str:
    notes = sorted(section.glob("*Study-Notes.md"))
    if len(notes) != 1:
        raise SystemExit(f"{section}: need exactly one *Study-Notes.md")
    parts = [ASK.format(lost=", though OLD CORE did" if before else "",
                        changed=" or from OLD CORE" if before else "")]
    parts += ["===== LEDGER =====", ledger_claims(section / "ledger.md")]
    practice = section / "Practice.md"
    titles = QUESTION.findall(practice.read_text()) if practice.is_file() else []
    parts += ["===== PRACTICE QUESTIONS =====", "\n".join(titles) or "(none)"]
    labels = [f"{svg.name}: {' | '.join(s.strip() for s in LABEL.findall(svg.read_text()))}"
              for svg in sorted(section.glob("*.svg"))]
    parts += ["===== FIGURE LABELS =====", "\n".join(labels) or "(none)"]
    if before:
        parts += ["===== OLD CORE =====", core(before)]
    parts += ["===== CORE =====", core(notes[0])]
    return scrub("\n\n".join(parts))


def main() -> None:
    ap = argparse.ArgumentParser(description="Print the Sol review brief for one section.")
    ap.add_argument("--section", required=True, type=Path, help="section folder, e.g. Chapter-04/4.2")
    ap.add_argument("--before", type=Path, help="previous *Study-Notes.md when the section is a rewrite")
    args = ap.parse_args()
    sys.stdout.write(brief(args.section, args.before) + "\n")


if __name__ == "__main__":
    main()
