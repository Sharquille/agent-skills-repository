from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCAFFOLD = SKILL_DIR / "scripts" / "kit_scaffold.py"
BUILD = SKILL_DIR / "scripts" / "build_anki_import.py"

NOTES = """# 5.2 Core

Intro text before the first group.

## A. Independence

### 1. Independent events

Two events are independent when one doesn't change the other's chance.

### 2. Conditional probability

```text
### 9. Not a topic inside a fence
```

P(A | B) is the chance of A given B.

## B. Multiplication rules

### 3. Independent events, formula (4)

P(A and B) = P(A) * P(B)

# 5.2 Retrieval

### 4. Not Core, after Retrieval
"""


class KitScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.course = Path(self.temporary.name) / "MA-235"
        for sec in ("5.2", "5.10"):
            d = self.course / "Chapter-Kits" / "Chapter-05" / sec
            d.mkdir(parents=True)
            (d / f"MA-235_Ch{sec}_Study-Notes.md").write_text(NOTES.replace("5.2", sec), encoding="utf-8")
            (d / "Practice.md").write_text("> [!question]- Q01. Not a card source\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def scaffold(self, chapter: str = "5") -> dict:
        out = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--course", str(self.course), "--chapter", chapter],
            check=True, capture_output=True, text=True,
        )
        return json.loads(out.stdout)

    def test_lists_core_topics_in_section_order(self) -> None:
        data = self.scaffold()
        self.assertEqual([s["section"] for s in data["sections"]], ["5.2", "5.10"])
        topics = data["sections"][0]["topics"]
        self.assertEqual([t["heading"] for t in topics], [
            "1. Independent events",
            "2. Conditional probability",
            "3. Independent events, formula (4)",
        ])

    def test_stops_at_retrieval_and_ignores_fenced_headings(self) -> None:
        headings = [t["heading"] for t in self.scaffold()["sections"][0]["topics"]]
        self.assertNotIn("4. Not Core, after Retrieval", headings)
        self.assertNotIn("9. Not a topic inside a fence", headings)

    def test_topic_body_ends_at_group_heading(self) -> None:
        first = self.scaffold()["sections"][0]["topics"][0]
        self.assertIn("one doesn't change the other's chance", first["body"])
        self.assertNotIn("Multiplication", first["body"])

    def test_identity_fields(self) -> None:
        data = self.scaffold("05")
        t = data["sections"][0]["topics"][2]
        self.assertEqual(t["objective"], "5.2 Core 3 · Independent events, formula (4)")
        self.assertEqual(t["source"], "Chapter-Kits/Chapter-05/5.2/MA-235_Ch5.2_Study-Notes.md#3. Independent events, formula (4)")
        self.assertEqual(t["id_prefix"], "ma-235.5-2.core-3")
        self.assertEqual(t["tags"], ["ma-235", "ch05", "sec-5-2", "core-3"])
        sk = data["skeleton"]
        self.assertEqual((sk["chapter_id"], sk["deck"], data["manifest_path"]), ("ma-235-ch05", "MA-235::Chapter 05", "_study/anki/ma-235-ch05.json"))

    def test_filled_skeleton_passes_the_generator(self) -> None:
        data = self.scaffold()
        manifest = data["skeleton"]
        topics = [t for s in data["sections"] for t in s["topics"]]
        manifest["cards"] = [
            {
                "id": f"{t['id_prefix']}.concept.basic",
                "objective": t["objective"],
                "type": "basic",
                "prompt": f"Recall prompt for {t['objective']}?",
                "answer": f"Answer for {t['objective']}.",
                "source": t["source"],
                "revision": 1,
                "status": "active",
                "tags": t["tags"],
            }
            for t in topics
        ]
        path = self.course / data["manifest_path"]
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        out = subprocess.run(
            [sys.executable, str(BUILD), str(path), "--vault", str(self.course)],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("#deck:MA-235::Chapter 05", out.stdout)

    def test_missing_chapter_is_an_error(self) -> None:
        out = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--course", str(self.course), "--chapter", "9"],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 1)
        self.assertIn("no chapter folder", out.stderr)


if __name__ == "__main__":
    unittest.main()
