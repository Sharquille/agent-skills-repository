#!/usr/bin/env python3
"""Write a one-time setup .apkg that installs the "Study Calc" note type in Anki.

Import it once per Anki profile (File > Import); after that, every chapter's
`<chapter>-calc.tsv` imports into that note type. Needs the third-party `genanki`
package, used only here: install it into a throwaway virtual environment
(`python3 -m venv /tmp/calc && /tmp/calc/bin/pip install genanki==0.13.1`) and run this
script with that interpreter. The templates live in assets/study-calc/; calc.js is
inlined into both sides where the `<!-- calc.js -->` marker sits.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "study-calc"
MODEL_ID = 1716150311  # fixed: re-importing updates the same note type instead of adding a copy
DECK_ID = 1716150313
FIELDS = ("Prompt", "Kind", "Params", "Method", "Source")
MARKER = "<!-- calc.js -->"


def template(name: str) -> str:
    html = (ASSETS / name).read_text(encoding="utf-8")
    if html.count(MARKER) != 1:
        raise SystemExit(f"{name} must contain {MARKER} exactly once")
    script = (ASSETS / "calc.js").read_text(encoding="utf-8")
    return html.replace(MARKER, f"<script>\n{script}</script>")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="path for the setup .apkg")
    args = parser.parse_args()
    import genanki  # imported late so --help works without it

    model = genanki.Model(
        MODEL_ID, "Study Calc",
        fields=[{"name": name} for name in FIELDS],
        templates=[{"name": "Calc", "qfmt": template("front.html"), "afmt": template("back.html")}],
        css=(ASSETS / "style.css").read_text(encoding="utf-8"),
    )
    deck = genanki.Deck(DECK_ID, "Study Calc setup")
    deck.add_note(genanki.Note(
        model=model,
        fields=["A fair coin is tossed {n} times. What is the probability of exactly {r} heads?",
                "binom-exact", json.dumps({"n": [4, 8], "p": [0.5]}),
                "Import this .apkg once; after that, delete this setup deck.", "setup"],
        guid=genanki.guid_for("study-calc.setup"),
    ))
    genanki.Package(deck).write_to_file(str(args.output))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
