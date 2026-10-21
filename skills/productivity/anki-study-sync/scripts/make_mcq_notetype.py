#!/usr/bin/env python3
"""Write a one-time setup .apkg that installs the "Study MCQ" note type in Anki.

Import it once per Anki profile (File > Import); after that, every chapter's
`<chapter>-quiz.tsv` imports into that note type. Needs the third-party `genanki`
package, used only here: install it into a throwaway virtual environment
(`python3 -m venv /tmp/mcq && /tmp/mcq/bin/pip install genanki==0.13.1`) and run this
script with that interpreter. The templates live in assets/study-mcq/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "study-mcq"
MODEL_ID = 1716150301  # fixed: re-importing updates the same note type instead of adding a copy
DECK_ID = 1716150303
FIELDS = ("Question", "A", "B", "C", "D", "Correct", "Why", "Source")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="path for the setup .apkg")
    args = parser.parse_args()
    import genanki  # imported late so --help works without it

    model = genanki.Model(
        MODEL_ID, "Study MCQ",
        fields=[{"name": name} for name in FIELDS],
        templates=[{"name": "MCQ", "qfmt": (ASSETS / "front.html").read_text(encoding="utf-8"),
                    "afmt": (ASSETS / "back.html").read_text(encoding="utf-8")}],
        css=(ASSETS / "style.css").read_text(encoding="utf-8"),
    )
    deck = genanki.Deck(DECK_ID, "Study MCQ setup")
    deck.add_note(genanki.Note(
        model=model,
        fields=["Which file installs the Study MCQ card style in Anki?", "This setup deck",
                "A chapter TSV", "An add-on", "A filtered deck", "A",
                "Import this .apkg once; after that, delete this setup deck.", "setup"],
        guid=genanki.guid_for("study-mcq.setup"),
    ))
    genanki.Package(deck).write_to_file(str(args.output))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
