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

    def test_coverage_flow(self):
        log = lambda item, res: c.log_attempt(self.s11, item, res, "r", "n", "2026-09-29")
        st = lambda: self.statuses({"1.1"})[("1.1", 1)]
        log("Core 1 · plain words", "missed")
        self.assertEqual(st(), "fragile")
        log("Core 1 · step 1 breakdown", "correct")          # breakdown steps teach, they don't count
        log("Core 1 · real-world map twin", "correct")
        self.assertEqual(st(), "developing")                # a miss owes two correct twins
        log("Core 1 · contrast twin", "correct")
        self.assertEqual(st(), "bug hunt")
        log("Core 1 · bug hunt", "correct")
        self.assertEqual(st(), "covered")

    def test_a_missed_bug_hunt_owes_two_and_two_misses_restart_teaching(self):
        log = lambda item, res: c.log_attempt(self.s11, item, res, "r", "n", "2026-09-29")
        rows = lambda: [r for r in c.read_log(self.s11) if "Core 2" in r["item"]]
        log("Core 2 · compute", "correct")
        log("Core 2 · bug hunt", "missed")
        self.assertEqual(c.progress(rows())["need"], 2)
        log("Core 2 · bug hunt", "correct")
        self.assertEqual(c.status(rows()), "bug hunt")      # both must be right
        log("Core 2 · bug hunt", "correct")
        self.assertEqual(c.status(rows()), "covered")
        log("Core 1 · compute", "correct")
        log("Core 1 · bug hunt", "missed")
        log("Core 1 · bug hunt", "missed")
        log("Core 1 · bug hunt", "missed")
        r1 = [r for r in c.read_log(self.s11) if "Core 1" in r["item"]]
        self.assertEqual(c.status(r1), "fragile")
        self.assertTrue(c.next_check(r1).startswith("re-teach first"))
        log("Core 1 · real-world map", "correct")              # re-taught, competency again, then a new bug hunt
        r1 = [r for r in c.read_log(self.s11) if "Core 1" in r["item"]]
        self.assertEqual(c.next_check(r1), "bug hunt: find and fix a planted mistake; pass = covered")

    def test_one_of_two_bug_hunts_earns_a_final_one(self):
        for item, res in [("compute", "correct"), ("bug hunt", "missed"), ("bug hunt", "correct"), ("bug hunt", "missed")]:
            c.log_attempt(self.s11, f"Core 2 · {item}", res, "r", "n", "2026-09-29")
        rows = [r for r in c.read_log(self.s11) if "Core 2" in r["item"]]
        self.assertEqual(c.next_check(rows), "final bug hunt: pass = covered, miss = re-teach")

    def test_practice_question_ids_map_through_the_plan(self):
        c.log_attempt(self.s11, "Q02", "correct", "sorted it", "2026-10-01, Core 2 · why it matters", "2026-09-27")
        data = c.scope(self.kit, sections={"1.1"})[0]["concepts"]
        core2 = next(k for k in data if k["core"] == 2)
        self.assertEqual((core2["status"], core2["attempts"]), ("bug hunt", 1))
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

    def test_scope_shows_coverage_and_covered_concepts_leave_the_table(self):
        c.log_attempt(self.s11, "Core 2 · real-world map", "partial", "r", "2026-10-01, Core 2 · contrast", "2026-09-27")
        core2 = next(k for k in c.scope(self.kit, sections={"1.1"})[0]["concepts"] if k["core"] == 2)
        self.assertEqual(core2["tried"], "real-world map ~")
        self.assertEqual(core2["check"], "1 correct twin in a new scenario")
        c.log_attempt(self.s11, "Core 2 · contrast twin", "correct", "r", "2026-10-01, Core 2 · bug hunt", "2026-09-28")
        c.log_attempt(self.s11, "Core 2 · bug hunt", "correct", "r", "—", "2026-09-29")
        text = c.render(c.scope(self.kit, chapters={1, 2}))
        self.assertIn("- Chapter 1: 1 of 2 covered · 1 outstanding (0 bug hunt due, 0 developing, 0 fragile, 1 not yet checked)", text)
        self.assertIn("Covered, not asked again: Core 2 Variable type", text)
        self.assertNotIn("| 2 | Variable type |", text.split("## 2.1")[0])

    def test_logging_syncs_the_queue_through_the_flow(self):
        course = self.kit.parent
        tracker = lambda: [(i["core"], i["kind"]) for i in c.load_tracker(course)["queue"]]
        c.log_attempt(self.s11, "Core 1 · contrast", "missed", "r", "2026-09-30, Core 1 · real-world map twin")
        st, new = c.follow_up(self.s11, "Core 1 · contrast", "missed", "2026-09-30, Core 1 · real-world map twin")
        self.assertEqual((st, len(new), new[0]["lens"]), ("fragile", 2, "real-world map twin"))
        c.log_attempt(self.s11, "Core 1 · step 1 breakdown", "partial", "r", "x")
        self.assertEqual(c.follow_up(self.s11, "Core 1 · step 1 breakdown", "partial", "x")[1], [])
        c.log_attempt(self.s11, "Core 2 · compute", "correct", "r", "2026-10-01, Core 2 · bug hunt")
        st, new = c.follow_up(self.s11, "Core 2 · compute", "correct", "2026-10-01, Core 2 · bug hunt")
        self.assertEqual((st, new[0]["kind"]), ("bug hunt", "bug hunt"))
        c.log_attempt(self.s11, "Core 2 · bug hunt", "correct", "r", "—")
        st, _ = c.follow_up(self.s11, "Core 2 · bug hunt", "correct", "—", answers=new[0]["id"])
        self.assertEqual(st, "covered")
        self.assertEqual(tracker(), [(1, "twin"), (1, "twin")])  # covered concepts leave the queue
        self.assertEqual(c.follow_up(self.kit, "Core 2 · compute", "correct", "x"), (None, []))  # not a section

    def test_sync_converts_entries_and_keeps_their_wait(self):
        course = self.kit.parent
        c.queue_cmd(course, "add", section="1.1", core=2, kind="harder", lens="stress test")
        for _ in range(4):
            c.queue_cmd(course, "tick")
        c.log_attempt(self.s11, "Core 2 · compute", "correct", "r", "n")
        c.sync_course(course)
        (entry,) = c.load_tracker(course)["queue"]
        self.assertEqual((entry["kind"], entry["lens"], entry["since"]), ("bug hunt", "bug hunt", 4))

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
