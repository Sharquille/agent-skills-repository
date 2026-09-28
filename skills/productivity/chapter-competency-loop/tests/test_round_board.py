import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round_board as rb  # noqa: E402

CARD = dict(section="1.1", concept="Levels", lens="real-world map", verdict="correct",
            ask="<p>Which level is each variable?</p>",
            parts=[("OS", "nominal", "nominal", True), ("Extra: Temp", "ratio", "interval", False)],
            why="Names only; Celsius has no true zero.", remember="Name what each level adds.")


MISSED = dict(CARD, verdict="missed", parts=[("Which uses chance?", "", "(b)", False)])


def round_(cards, **extra):
    return dict(course="MA-235", scope="Chapters 1–3", date="2026-09-27", number=1, planned=8,
                slug="t-r1", cards=cards, **extra)


class RoundBoardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name) / "Work"
        self.work.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_card_shows_the_full_question_and_maps_each_part(self):
        out, _ = rb.build(round_([CARD, dict(CARD, wide=True)]), work=self.work)
        text = out.read_text()
        self.assertIn("Question, as asked", text)
        self.assertIn("<p>Which level is each variable?</p>", text)
        self.assertIn('<tr class="ok"><td>OS</td>', text)
        self.assertIn('<tr class="no"><td>Extra: Temp</td><td class="yours">ratio</td><td class="correct">interval</td>', text)
        self.assertEqual(rb.eli5.check(text, max_words=rb.MAX_WORDS)[0], [])
        self.assertIn("## Competency rounds", (self.work / "README.md").read_text())
        self.assertIn('class="explain wide"', text)

    def test_open_question_sits_first_and_tiles_link_to_cards(self):
        missed = dict(MISSED, concept="Sampling")
        r = round_([CARD, missed], current=dict(num="Q2 · step 1", meta="breakdown", ask="<p>Step one?</p>"), queued=2)
        out, _ = rb.build(r, work=self.work)
        text = out.read_text()
        self.assertLess(text.index('id="now"'), text.index('id="q2"'))
        self.assertLess(text.index('id="q2"'), text.index('id="q1"'))  # newest card first
        self.assertIn('href="#q1"', text)
        self.assertIn('href="#now">Q2 · step 1</a>', text)
        self.assertIn("2 re-checks coming later", text)
        self.assertNotIn("re-check: Sampling", text)
        readme = (self.work / "README.md").read_text()
        self.assertEqual(sum("competency-t-r1.html" in ln for ln in readme.splitlines()), 1)

    def test_terms_are_defined_on_cards_and_the_open_question(self):
        card = dict(CARD, terms=[("chance", "a random process picks, not a person")])
        r = round_([card, CARD], current=dict(ask="<p>Which uses chance?</p>", terms=[("chance", "defined")]))
        out, _ = rb.build(r, work=self.work)
        text = out.read_text()
        self.assertEqual(text.count("Words used here"), 2)
        self.assertIn("<dt>chance</dt><dd>a random process picks, not a person</dd>", text)

    def test_breakdown_steps_are_labeled_and_not_counted(self):
        step = dict(MISSED, step=True, num="Q2 · step 0")
        r = round_([CARD, MISSED, step], current=dict(step=True, num="Q2 · step 0b", ask="<p>?</p>"))
        out, _ = rb.build(r, work=self.work)
        text = out.read_text()
        self.assertIn('href="#q3">Q2 · step 0</a>', text)
        self.assertIn('href="#now">Q2 · step 0b</a>', text)
        self.assertIn('<span class="tile">Q3</span>', text)
        self.assertIn("1 correct of 2 answered", text)

    def test_context_and_help_menu_are_on_the_board(self):
        r = round_([CARD, CARD], context={"Goal": "Exam 1 prep", "Exam": "2026-10-01", "Saved in": "Week 4"})
        out, _ = rb.build(r, work=self.work)
        text = out.read_text()
        self.assertIn("Goal: <b>Exam 1 prep</b>", text)
        self.assertIn("Help menu", text)
        self.assertIn("<dt>move files to week N</dt>", text)

    def test_audit_blocks_marks_that_contradict_the_verdict(self):
        cases = {
            "direct-answer row (first) is marked right": dict(CARD, verdict="missed",
                parts=[("Which uses chance?", "(c)", "(b)", True)]),
            "a non-extra row is marked wrong": dict(CARD, verdict="correct",
                parts=[("OS", "nominal", "nominal", True), ("Temp", "ratio", "interval", False)]),
            "answer is blank": dict(CARD, verdict="partial", parts=[("Q", "", "x", True)]),
            "matches the correct answer": dict(CARD, verdict="partial", parts=[("Q", "b", "b", False)]),
            "not an extra": dict(CARD, verdict="partial", parts=[("Extra: name", "x", "y", False)]),
        }
        for message, card in cases.items():
            with self.subTest(message):
                with self.assertRaises(ValueError) as ctx:
                    rb.build(round_([card, CARD]), work=self.work)
                self.assertIn(message, str(ctx.exception))
        ok = dict(CARD, parts=[("OS", "nominal", "nominal", True), ("Extra: note", "x", "y", False)])
        self.assertEqual(rb.audit(round_([ok])), [])

    def test_refuses_to_overwrite_a_non_board_file(self):
        target = self.work / "competency-t-r1.html"
        target.write_text("my notes")
        with self.assertRaises(ValueError):
            rb.build(round_([CARD]), work=self.work)
        self.assertEqual(target.read_text(), "my notes")


if __name__ == "__main__":
    unittest.main()
