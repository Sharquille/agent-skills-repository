#!/usr/bin/env python3
"""Print the obsidian-study-loop plain-language manual, whole or by topic.

Usage:
  study_man.py            print the full manual
  study_man.py --list     list topics (id + title)
  study_man.py <topic>    print matching section(s); topic matches a section
                          id, an alias, or a keyword in either

Read-only: parses references/manpage.md next to this skill and prints to
stdout. No network, no vault access, no writes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MANPAGE = Path(__file__).resolve().parent.parent / "references" / "manpage.md"

SECTION_RE = re.compile(
    r"<!--\s*man:section\s+id=(?P<id>[a-z0-9-]+)"
    r'(?:\s+aliases="(?P<aliases>[^"]*)")?\s*-->\n'
    r"(?P<body>.*?)"
    r"<!--\s*man:section-end\s+id=(?P=id)\s*-->",
    re.DOTALL,
)


def load_sections(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"error: cannot read manual at {path}: {exc}\n")
        raise SystemExit(2)
    sections = []
    for match in SECTION_RE.finditer(text):
        body = match.group("body").strip("\n")
        heading = next(
            (line for line in body.splitlines() if line.startswith("## ")), ""
        )
        aliases = [
            alias.strip().lower()
            for alias in (match.group("aliases") or "").split(",")
            if alias.strip()
        ]
        sections.append(
            {
                "id": match.group("id"),
                "aliases": aliases,
                "title": heading[3:].strip() or match.group("id"),
                "body": body,
            }
        )
    if not sections:
        sys.stderr.write(f"error: no man:section markers found in {path}\n")
        raise SystemExit(2)
    return sections


def match_score(section: dict, query: str) -> int:
    q = query.lower().strip()
    if not q:
        return 0
    if q == section["id"]:
        return 3
    if q in section["aliases"]:
        return 2
    haystack = " ".join(
        [section["id"], " ".join(section["aliases"]), section["title"].lower()]
    )
    return 1 if q in haystack else 0


def print_list(sections: list[dict]) -> None:
    width = max(len(s["id"]) for s in sections)
    print("Topics (study_man.py <topic>):\n")
    for section in sections:
        print(f"  {section['id']:<{width}}  {section['title']}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Print the obsidian-study-loop manual, whole or by topic."
    )
    parser.add_argument("topic", nargs="*", help="topic id, alias, or keyword")
    parser.add_argument(
        "--list", action="store_true", help="list topic ids and titles"
    )
    args = parser.parse_args(argv)

    sections = load_sections(MANPAGE)

    if args.list:
        print_list(sections)
        return 0

    if not args.topic:
        print("\n\n".join(section["body"] for section in sections))
        return 0

    query = " ".join(args.topic)
    scored = [(match_score(s, query), s) for s in sections]
    best = max(score for score, _ in scored)
    if best == 0:
        sys.stderr.write(f"no topic matches {query!r}\n\n")
        print_list(sections)
        return 1
    hits = [s for score, s in scored if score == best]
    print("\n\n".join(section["body"] for section in hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
