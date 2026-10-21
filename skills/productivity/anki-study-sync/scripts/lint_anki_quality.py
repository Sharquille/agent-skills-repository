#!/usr/bin/env python3
"""Lint vault Anki manifests for mixed-review quality. Read-only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from anki_quality import leak_warnings, official_acronyms, overlap_warnings, quality_errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument(
        "--strict-overlap",
        action="store_true",
        help="Fail when any course-wide overlap warning remains (use before a deck handoff)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        action="append",
        dest="manifests",
        help="Limit to one or more manifest paths (repeatable). Default: all JSON under _study/anki/",
    )
    return parser.parse_args()


def load_cards(path: Path) -> list[object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{path}: cannot read manifest: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
        raise RuntimeError(f"{path}: manifest cards must be a list")
    return data["cards"]


def main() -> int:
    args = parse_args()
    vault = args.vault.expanduser().resolve()
    handoff = (vault / "_study" / "anki").resolve()
    if args.manifests:
        paths = [path.expanduser().resolve() for path in args.manifests]
    else:
        if not handoff.is_dir():
            print(f"ERROR: missing Anki handoff directory: {handoff}", file=sys.stderr)
            return 1
        paths = sorted(handoff.glob("*.json"))
    failed = 0
    decks: dict[str, list[object]] = {}
    for path in paths:
        try:
            if not path.is_relative_to(handoff):
                print(f"ERROR: {path} is outside {handoff}", file=sys.stderr)
                failed += 1
                continue
            cards = load_cards(path)
            decks[path.name] = cards
            findings = quality_errors(cards)
            for warning in leak_warnings(cards):
                print(f"warning: {path.name}: {warning}", file=sys.stderr)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failed += 1
            continue
        if findings:
            failed += 1
            print(f"ERROR: {path.name}", file=sys.stderr)
            for finding in findings:
                print(f"  {finding}", file=sys.stderr)
    acronyms_md = vault / "Chapter-Kits" / "acronyms.md"
    official = official_acronyms(acronyms_md.read_text(encoding="utf-8")) if acronyms_md.is_file() else frozenset()
    overlaps = overlap_warnings(decks, official)
    for warning in overlaps:
        print(f"warning: {warning}", file=sys.stderr)
    if overlaps and args.strict_overlap:
        print(f"ERROR: {len(overlaps)} course-wide overlap warning(s) remain", file=sys.stderr)
        failed += 1
    if failed:
        return 1
    print(f"OK: {len(paths)} Anki manifest(s) passed mixed-review checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
