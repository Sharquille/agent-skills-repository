import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import competency as c  # noqa: E402

NOTES = """# 1.1 Core

## 1. Two definitions

### 2. Variable type

**TEST MOVE:** sort it.

# 1.1 Quiz why

### 3. Hidden worked item
"""

PLAN = """Q_min = A + H = 2 + 0 = 2
| Outcome | Core/source anchor | Learner decision | r_i | Primary | Extra |
| --- | --- | --- | --- | --- | --- |
| 1 | Core 1, S001 | Define | — | Q01 foundation | — |
| 2 | Core 2, S001 | Sort type | — | Q02 foundation | — |
"""


class CompetencyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        course = Path(self.tmp.name) / "MA-235"
        self.kit = course / "Chapter-Kits"
        self.s11 = self.make_section("Chapter-01", "1.1", 1, "Data Basics")
        self.s21 = self.make_section("Chapter-02", "2.1", 2, "Frequency Tables")
        work = course / "Week-01_2026-09-09_to_2026-09-13" / "Work"
        work.mkdir(parents=True)
        (work / "basics-eli5.html").write_text("<p data-step=1>")
        (work / "sampling-eli5.html").write_text("<p data-step=1>")
        (work / "README.md").write_text(
            "## ELI5 explainers\n\n"
            "- [`basics-eli5.html`](basics-eli5.html) — basics (section 1.1).\n"
            "- [`sampling-eli5.html`](sampling-eli5.html) — sampling (section 1.2).\n")

    def tearDown(self):
        self.tmp.cleanup()

    def make_section(self, chapter, sid, week, title):
        sec = self.kit / chapter / sid
        sec.mkdir(parents=True)
        (sec / "state.json").write_text(json.dumps({"week": week, "title": title}))
        (sec / f"X_Ch{sid}_Study-Notes.md").write_text(NOTES)
        (sec / "practice-plan.md").write_text(PLAN)
        return sec

    def statuses(self, sections=None, chapters=None):
        data = c.scope(self.kit, chapters=chapters, sections=sections)
        return {(s["section"], k["core"]): k["status"] for s in data for k in s["concepts"]}

    def test_concepts_stop_at_quiz_why_and_start_unassessed(self):
        data = c.scope(self.kit, sections={"1.1"})
        self.assertEqual([(k["core"], k["title"]) for k in data[0]["concepts"]],
                         [(1, "Two definitions"), (2, "Variable type")])
        self.assertEqual({k["status"] for k in data[0]["concepts"]}, {"unassessed"})

    def test_chapter_and_section_filters(self):
        self.assertEqual([s["section"] for s in c.scope(self.kit, chapters={1})], ["1.1"])
        self.assertEqual([s["section"] for s in c.scope(self.kit, chapters=c.chapter_range("1-2"))], ["1.1", "2.1"])
        self.assertEqual([s["section"] for s in c.scope(self.kit, sections={"2.1"})], ["2.1"])

    def test_eli5_pages_are_matched_to_their_section(self):
        pages = c.scope(self.kit, sections={"1.1"})[0]["eli5"]
        self.assertEqual([Path(p["file"]).name for p in pages], ["basics-eli5.html"])
        self.assertTrue(c.covers("walkthrough (sections 3.1–3.2).", "3.2"))
        self.assertFalse(c.covers("walkthrough (sections 3.1–3.2).", "3.3"))
        self.assertTrue(c.covers("no section named", "9.9"))

    def test_status_rules(self):
        log = lambda item, res, date: c.log_attempt(self.s11, item, res, "r", "n", date)
        log("Core 1 · plain words", "missed", "2026-09-20")
        self.assertEqual(self.statuses({"1.1"})[("1.1", 1)], "fragile")
        log("Core 1 · real-world map", "correct", "2026-09-21")
        log("Core 1 · contrast", "correct", "2026-09-21")
        log("Core 1 · contrast", "correct", "2026-09-21")
        self.assertEqual(self.statuses({"1.1"})[("1.1", 1)], "developing")  # one date only
        log("Core 1 · teach-back", "correct", "2026-09-24")
        log("Core 1 · real-world map", "correct", "2026-09-28")
        self.assertEqual(self.statuses({"1.1"})[("1.1", 1)], "secure")
        log("Core 1 · stress test", "partial", "2026-10-01")
        self.assertEqual(self.statuses({"1.1"})[("1.1", 1)], "fragile")

    def test_practice_question_ids_map_through_the_plan(self):
        c.log_attempt(self.s11, "Q02", "correct", "sorted it", "2026-10-01, Core 2 · why it matters", "2026-09-27")
        data = c.scope(self.kit, sections={"1.1"})[0]["concepts"]
        core2 = next(k for k in data if k["core"] == 2)
        self.assertEqual((core2["status"], core2["attempts"]), ("developing", 1))
        self.assertEqual(core2["next"], "2026-10-01, Core 2 · why it matters")

    def test_log_writes_the_kit_table_and_rejects_bad_input(self):
        c.log_attempt(self.s11, "Core 2 · compute", "partial", "slip", "2026-09-30, Core 2 · anatomy", "2026-09-27")
        text = (self.s11 / "study-log.md").read_text()
        self.assertIn("| Date | Item | Result | Reason given | Next review |", text)
        self.assertIn("| 2026-09-27 | Core 2 · compute | partial | slip | 2026-09-30, Core 2 · anatomy |", text)
        with self.assertRaises(ValueError):
            c.log_attempt(self.s11, "Core 2", "maybe", "r", "n")
        with self.assertRaises(ValueError):
            c.log_attempt(self.s11, "Core 2 | extra", "correct", "r", "n")
        with self.assertRaises(ValueError):
            c.log_attempt(self.kit, "Core 2", "correct", "r", "n")

    def test_cli(self):
        self.assertEqual(c.main(["scope", "--kit", str(self.kit), "--chapters", "1-3"]), 0)
        self.assertEqual(c.main(["scope", "--kit", str(self.kit), "--chapters", "7"]), 1)


if __name__ == "__main__":
    unittest.main()
