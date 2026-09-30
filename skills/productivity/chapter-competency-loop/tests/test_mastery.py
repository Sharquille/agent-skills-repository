import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import competency as comp  # noqa: E402
import mastery  # noqa: E402
import round_board as rb  # noqa: E402

NOTES = """# 2.1 Core

## 1. Class width

### 2. Class boundaries

# 2.1 Quiz why
"""


def card(num, cores, verdict="correct", step=False):
    return dict(num=num, section="2.1", concept="Boundaries", lens="bug hunt", verdict=verdict, step=step,
                cores=cores, ask="<p>Find the mistake.</p>",
                parts=[("The fix", "7.5 to 15.5", "7.5 to 15.5", True)] if verdict == "correct"
                else [("The fix", "8.5 to 14.5", "7.5 to 15.5", False)],
                why="Halfway to the neighbors.", remember="Move limits outward.", next="Covered: not asked again")


class MasteryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.course = Path(self.tmp.name) / "MA-235"
        self.sec = self.course / "Chapter-Kits" / "Chapter-02" / "2.1"
        self.sec.mkdir(parents=True)
        (self.sec / "state.json").write_text(json.dumps({"week": 2, "title": "Frequency Tables"}))
        (self.sec / "X_Ch2.1_Study-Notes.md").write_text(NOTES)
        self.work = self.course / "Week-04_2026-09-28_to_2026-10-04" / "Work"
        self.work.mkdir(parents=True)
        r = dict(course="MA-235", scope="Chapters 1–3", date="2026-09-29", number=2, planned=2, slug="t-r2",
                 cards=[card("Q1", [1], "missed"), card("Q2", [2])])
        self.board, _ = rb.build(r, work=self.work)

    def tearDown(self):
        self.tmp.cleanup()

    def log(self, core, item, result):
        comp.log_attempt(self.sec, f"Core {core} · {item}", result, "r", "n", "2026-09-29")

    def test_nothing_moves_until_a_topic_is_covered(self):
        self.log(2, "compute", "correct")  # competency shown, bug hunt still owed
        mastery.sync(self.course)
        self.assertFalse((self.course / "Mastery").exists())
        self.assertIn("Q2", self.board.read_text())

    def test_covered_cards_move_to_the_chapter_file_and_come_back_if_coverage_is_lost(self):
        self.log(2, "compute", "correct")
        self.log(2, "bug hunt", "correct")
        mastery.sync(self.course)
        page = self.course / "Mastery" / "Chapter 2 Mastery.html"
        text = page.read_text()
        self.assertIn("Chapter 2 mastery", text)
        self.assertIn("Core 2</b> Class boundaries", text)
        self.assertIn('id="r2-q2"', text)
        self.assertIn("1 of 2", text)
        board = self.board.read_text()
        self.assertIn("../../Mastery/Chapter%202%20Mastery.html#r2-q2", board)  # the tile links to its new home
        self.assertNotIn('<span class="qnum">Q2</span>', board)
        self.assertIn('<span class="qnum">Q1</span>', board)             # the missed topic stays for review
        self.assertIn("(Chapter%202%20Mastery.html)", (self.course / "Mastery" / "README.md").read_text())
        self.assertEqual(rb.load_round(rb.record_path(self.board))["cards"][1].get("moved_to"), None)
        # asked again and wrong: the topic is no longer covered, so its card returns to the board
        self.log(2, "real-world map", "missed")
        mastery.sync(self.course)
        self.assertIn('<span class="qnum">Q2</span>', self.board.read_text())
        self.assertIn("0 of 2", page.read_text())

    def test_review_cue_links_the_earlier_cards_for_this_rounds_rechecks(self):
        r = dict(course="MA-235", scope="Chapters 1–3", date="2026-09-30", number=3, planned=8, slug="t-r3",
                 review=[("2.1", 1), ("2.1", 2)], cards=[],
                 current=dict(num="Q1", ask="<p>Twin.</p>", recheck=("2.1", 1)))
        rb.attach_review(r, self.course, self.work)
        board, _ = rb.build(r, work=self.work)
        text = board.read_text()
        self.assertIn("Review before this round", text)
        self.assertIn('href="Round%202%20-%20Chapters%201-3%20%28Sep%2029%29.html#q1">Round 2 · Q1</a>', text)
        self.assertIn('href="Round%202%20-%20Chapters%201-3%20%28Sep%2029%29.html#q2">Round 2 · Q2</a>', text)
        self.assertIn("Re-check: review", text)
        rec = rb.load_round(rb.record_path(board))
        self.assertNotIn("review_links", rec)                  # links are rebuilt from the records, not saved
        self.assertEqual(rec["review"], [["2.1", 1], ["2.1", 2]])


if __name__ == "__main__":
    unittest.main()
