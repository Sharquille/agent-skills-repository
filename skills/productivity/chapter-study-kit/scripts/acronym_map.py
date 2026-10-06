#!/usr/bin/env python3
"""Write a security kit's acronyms.md: the exam's official acronym list and where the notes use each.

First run takes the list from a JSON file of [short form, spelled out] pairs
extracted from the official objectives PDF; later runs reread acronyms.md and
refresh only the Where column. Stdlib only; no network.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import validate_kit

HEADER = """# Exam acronyms

The exam's official acronym list (source: {source}). **Where** names the
sections whose Core uses the acronym; each of those sections spells it out in
its Abbreviations table. **later module** means no section on hand uses it yet.
Regenerate after a rewrite: `acronym_map.py --kit <Chapter-Kits>`.

| Acronym | Spelled out | Where |
| --- | --- | --- |
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit", required=True, type=Path)
    ap.add_argument("--from-json", type=Path, help="[[short, spelled out], ...] from the official list")
    ap.add_argument("--source", default="the exam objectives PDF", help="where the list came from")
    args = ap.parse_args()
    kit = args.kit.resolve()
    if args.from_json:
        rows = [(short, spelled) for short, spelled in json.loads(args.from_json.read_text())]
    else:
        rows = [(short, spelled) for short, spelled, _ in validate_kit.read_acronyms(kit)]
        if not rows:
            raise SystemExit("no acronyms.md yet; pass --from-json")
    index = validate_kit.acronym_index(validate_kit.section_folders(kit), {r[0] for r in rows})
    body = "".join(f"| {short} | {spelled} | {', '.join(index[short]) or 'later module'} |\n"
                   for short, spelled in rows)
    (kit / "acronyms.md").write_text(HEADER.format(source=args.source) + body)
    used = sum(1 for short, _ in rows if index[short])
    print(f"{len(rows)} acronyms; {used} used in the notes on hand")


if __name__ == "__main__":
    main()
