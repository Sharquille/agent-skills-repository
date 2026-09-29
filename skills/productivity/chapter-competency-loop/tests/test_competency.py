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

    def test_scope_shows_lenses_tried_and_the_next_check(self):
        c.log_attempt(self.s11, "Core 2 · real-world map", "correct", "r", "2026-10-01, Core 2 · error hunt", "2026-09-27")
        core2 = next(k for k in c.scope(self.kit, sections={"1.1"})[0]["concepts"] if k["core"] == 2)
        self.assertEqual(core2["tried"], "real-world map ✓")
        self.assertTrue(core2["check"].startswith("retention: error hunt"))
        c.log_attempt(self.s11, "Core 2 · error hunt twin", "correct", "r", "2026-10-05, Core 2 · contrast", "2026-09-29")
        core2 = next(k for k in c.scope(self.kit, sections={"1.1"})[0]["concepts"] if k["core"] == 2)
        self.assertTrue(core2["check"].startswith("retention: stress test"))  # never the passed error hunt again
        c.log_attempt(self.s11, "Core 2 · stress test", "correct", "r", "2026-10-09, Core 2 · teach-back", "2026-10-02")
        rows = [r for r in c.read_log(self.s11) if "Core 2" in r["item"]]
        self.assertEqual(c.next_check(rows, today="2026-10-03"), "secure: don't ask before 2026-10-09, then retention contrast")
        text = c.render(c.scope(self.kit, chapters={1, 2}))
        self.assertIn("- Chapter 1: 2 concepts · 1 checked (1 secure, 0 developing, 0 fragile) · 1 not yet checked", text)

    def test_every_scored_answer_queues_its_follow_up(self):
        course = self.kit.parent
        new = c.follow_up(self.s11, "Core 2 · compute", "correct", "2026-10-01, Core 2 · error hunt")
        self.assertEqual([(i["kind"], i["lens"], i["due"]) for i in new], [("harder", "error hunt", "2026-10-01")])
        self.assertEqual(len(c.follow_up(self.s11, "Core 1 · contrast", "missed", "2026-09-30, Core 1 · twin")), 2)
        self.assertEqual(c.follow_up(self.s11, "Core 1 · step 1 breakdown", "partial", "2026-09-30, Core 1 · twin"), [])
        hedged = c.follow_up(self.s11, "Core 2 · predict", "correct", "2026-10-01, Core 2 · anatomy", kind="same")
        self.assertEqual(hedged[0]["kind"], "same")
        # answering a queued re-check closes it
        c.follow_up(self.s11, "Core 2 · error hunt twin", "partial", "2026-10-02, Core 2 · contrast", answers=new[0]["id"])
        ids = [i["id"] for i in c.load_tracker(course)["queue"]]
        self.assertNotIn(new[0]["id"], ids)
        self.assertEqual(c.follow_up(self.kit, "Core 2 · compute", "correct", "x"), [])  # not a section

    def test_secure_concepts_stop_coming_back(self):
        for day in ("2026-09-27", "2026-09-29", "2026-10-02"):
            lens = "compute" if day != "2026-10-02" else "contrast"
            c.log_attempt(self.s11, f"Core 2 · {lens}", "correct", "r", "2026-10-09, Core 2 · teach-back", day)
        self.assertEqual(c.follow_up(self.s11, "Core 2 · contrast", "correct", "2026-10-09, Core 2 · teach-back"), [])

    def make_weeks(self):
        course = self.kit.parent
        for name in ("Week-03_2026-09-21_to_2026-09-27", "Week-04_2026-09-28_to_2026-10-04",
                     "Weeks-14-15_Finals_2026-12-07_to_2026-12-17"):
            (course / name / "Work").mkdir(parents=True, exist_ok=True)
        return course

    def test_week_for_a_date_including_finals(self):
        course = self.make_weeks()
        self.assertEqual(c.week_for(course, "2026-09-28")["week"], 4)
        self.assertEqual(c.week_for(course, "2026-09-27")["week"], 3)
        self.assertEqual(c.week_for(course, "2026-12-15")["week"], 14)
        with self.assertRaises(ValueError):
            c.week_for(course, "2027-01-05")

    def test_tracker_set_resolves_the_work_folder_and_rejects_unknown_keys(self):
        course = self.make_weeks()
        data = c.tracker_set(course, ["goal=Exam 1 prep", "chapters=1-3", "week=4"])
        self.assertTrue(data["work"].endswith("Week-04_2026-09-28_to_2026-10-04/Work"))
        self.assertEqual(c.load_tracker(course)["goal"], "Exam 1 prep")
        self.assertTrue(c.tracker_set(course, ["week=15"])["work"].endswith("Finals_2026-12-07_to_2026-12-17/Work"))
        with self.assertRaises(ValueError):
            c.tracker_set(course, ["color=blue"])

    def test_queue_waits_for_the_gap(self):
        course = self.make_weeks()
        c.queue_cmd(course, "add", section="1.2", core=4, kind="twin", count=2, gap=3)
        c.queue_cmd(course, "add", section="1.1", core=7, kind="harder", gap=3)
        for _ in range(2):
            c.queue_cmd(course, "tick")
        self.assertEqual(c.queue_cmd(course, "due"), [])
        c.queue_cmd(course, "tick")
        due = c.queue_cmd(course, "due")
        self.assertEqual(len(due), 3)
        c.queue_cmd(course, "done", qid=due[0]["id"])
        self.assertEqual(len(c.load_tracker(course)["queue"]), 2)

    def test_cli(self):
        self.assertEqual(c.main(["scope", "--kit", str(self.kit), "--chapters", "1-3"]), 0)
        self.assertEqual(c.main(["scope", "--kit", str(self.kit), "--chapters", "7"]), 1)


if __name__ == "__main__":
    unittest.main()
