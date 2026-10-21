#!/usr/bin/env python3
"""List subjects that more than one active card asks about, across every manifest in a vault.

Read-only review aid for "one card per idea": word-level overlap checks miss two cards
that ask the same thing in different words. Read each group and keep one card unless the
cards test different facets (what X is vs when to use X).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

STOP = set(
    "what which how does do is are the a an of to and or in on for with by from that this its it be as at your "
    "you can when why who name four three two five one each other should between differ difference different "
    "like such about into than more most kind kinds type types use used make makes".split()
)


def subjects(prompt: str) -> set[str]:
    acronyms = set(re.findall(r"\b[A-Z][A-Z0-9]{1,6}s?\b", prompt))
    words = [w for w in re.findall(r"[a-z][a-z-]+", prompt.lower()) if w not in STOP and len(w) > 3]
    return acronyms | {f"{a} {b}" for a, b in zip(words, words[1:])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--min", type=int, default=2, help="smallest group to show (default 2)")
    args = parser.parse_args()
    index: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path in sorted((args.vault / "_study" / "anki").glob("*.json")):
        for card in json.loads(path.read_text(encoding="utf-8")).get("cards", []):
            if card.get("status") != "active":
                continue
            for subject in subjects(card.get("prompt", "")):
                index[subject].append((path.name, card.get("id", ""), card.get("prompt", "")))
    shown: set[tuple[str, ...]] = set()
    for subject, rows in sorted(index.items(), key=lambda item: -len(item[1])):
        key = tuple(sorted(row[1] for row in rows))
        if len(rows) < args.min or key in shown:
            continue
        shown.add(key)
        decks = sorted({row[0] for row in rows})
        print(f"## {subject} ({len(rows)} cards; {', '.join(decks)})")
        for deck, card_id, prompt in rows:
            print(f"  {card_id}: {prompt}")
    print(f"{len(shown)} subject group(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
