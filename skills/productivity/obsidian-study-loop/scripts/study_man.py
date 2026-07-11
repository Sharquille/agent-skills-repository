#!/usr/bin/env python3
"""Print the obsidian-study-loop plain-language manual, whole or by topic.

Usage:
  study_man.py            print the full manual
  study_man.py --list     list topics (id + title)
  study_man.py <topic>    print matching section(s); topic matches a section
                          id, an alias, or a keyword in either
  study_man.py --pretty   force the styled terminal view (ANSI); --raw forces
                          plain markdown. Default: styled on an interactive
                          terminal, plain markdown when piped.

Read-only: parses references/manpage.md next to this skill and prints to
stdout. No network, no vault access, no writes.
"""

from __future__ import annotations

import argparse
import os
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


PALETTE = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "heading": "\033[1;36m",
    "rule": "\033[36m",
    "code": "\033[33m",
}

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")


def strip_inline(text: str) -> str:
    return CODE_RE.sub(r"\1", BOLD_RE.sub(r"\1", text))


def style_inline(text: str) -> str:
    text = BOLD_RE.sub(
        lambda m: PALETTE["bold"] + m.group(1) + PALETTE["reset"], text
    )
    return CODE_RE.sub(
        lambda m: PALETTE["code"] + m.group(1) + PALETTE["reset"], text
    )


def format_table(rows: list[str]) -> list[str]:
    parsed = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if cells and all(set(cell) <= set("-: ") for cell in cells):
            continue
        parsed.append([strip_inline(cell) for cell in cells])
    if not parsed:
        return []
    ncol = max(len(row) for row in parsed)
    for row in parsed:
        row.extend([""] * (ncol - len(row)))
    widths = [max(len(row[i]) for row in parsed) for i in range(ncol)]
    out = []
    for index, row in enumerate(parsed):
        line = "  " + "   ".join(
            row[i].ljust(widths[i]) for i in range(ncol)
        ).rstrip()
        if index == 0:
            out.append(PALETTE["bold"] + line + PALETTE["reset"])
            out.append("  " + "   ".join("─" * widths[i] for i in range(ncol)))
        else:
            out.append(line)
    return out


def render_pretty(body: str) -> str:
    out: list[str] = []
    table: list[str] = []
    in_fence = False

    def flush_table() -> None:
        if table:
            out.extend(format_table(table))
            table.clear()

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_table()
            in_fence = not in_fence
            continue
        if in_fence:
            out.append("    " + PALETTE["dim"] + line + PALETTE["reset"])
            continue
        if stripped.startswith("|"):
            table.append(line)
            continue
        flush_table()
        if line.startswith("## "):
            title = strip_inline(line[3:])
            out.append("")
            out.append(PALETTE["heading"] + title.upper() + PALETTE["reset"])
            out.append(PALETTE["rule"] + "─" * min(len(title), 62) + PALETTE["reset"])
        elif line.startswith("### "):
            out.append(PALETTE["bold"] + strip_inline(line[4:]) + PALETTE["reset"])
        else:
            out.append(style_inline(line))
    flush_table()
    return "\n".join(out)


def use_pretty(args: argparse.Namespace) -> bool:
    if args.raw:
        return False
    if args.pretty:
        return True
    return sys.stdout.isatty() and os.environ.get("TERM", "dumb") != "dumb"


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


def print_list(sections: list[dict], pretty: bool) -> None:
    width = max(len(s["id"]) for s in sections)
    print("Topics (study_man.py <topic>):\n")
    for section in sections:
        topic_id = section["id"].ljust(width)
        if pretty:
            topic_id = PALETTE["bold"] + topic_id + PALETTE["reset"]
        print(f"  {topic_id}  {section['title']}")


def emit(sections: list[dict], pretty: bool) -> None:
    body = "\n\n".join(section["body"] for section in sections)
    print(render_pretty(body) if pretty else body)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Print the obsidian-study-loop manual, whole or by topic."
    )
    parser.add_argument("topic", nargs="*", help="topic id, alias, or keyword")
    parser.add_argument(
        "--list", action="store_true", help="list topic ids and titles"
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="force the styled terminal view (default on interactive terminals)",
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="force plain markdown output (default when piped)",
    )
    args = parser.parse_args(argv)
    pretty = use_pretty(args)

    sections = load_sections(MANPAGE)

    if args.list:
        print_list(sections, pretty)
        return 0

    if not args.topic:
        emit(sections, pretty)
        return 0

    query = " ".join(args.topic)
    scored = [(match_score(s, query), s) for s in sections]
    best = max(score for score, _ in scored)
    if best == 0:
        sys.stderr.write(f"no topic matches {query!r}\n\n")
        print_list(sections, pretty)
        return 1
    emit([s for score, s in scored if score == best], pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
