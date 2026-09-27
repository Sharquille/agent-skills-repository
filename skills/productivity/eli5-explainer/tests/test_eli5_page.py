import copy
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import eli5  # noqa: E402
import eli5_page  # noqa: E402

EXAMPLE = SKILL / "references" / "example_spec.py"


class BuilderTest(unittest.TestCase):
    def setUp(self):
        self.page = eli5_page.load_page(str(EXAMPLE))
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make_week(self, course="MA-235", name="Week-03_2026-09-21_to_2026-09-27"):
        work = self.root / course / name / "Work"
        work.mkdir(parents=True)
        return work

    def test_rendered_example_passes_the_checker(self):
        errors, parsed = eli5.check(eli5_page.render(self.page))
        self.assertEqual(errors, [])
        self.assertEqual(len(parsed.steps), 2)
        self.assertIn("Analogy, not from the source", eli5_page.render(self.page))

    def test_root_mode_writes_to_week_work_and_lists_it_once(self):
        work = self.make_week()
        (work / "README.md").write_text("# Week 3 Work\n")
        out, _ = eli5_page.build(self.page, root=str(self.root))
        self.assertEqual(Path(out), work / "median-eli5.html")
        eli5_page.build(self.page, root=str(self.root))  # rebuild in place
        readme = (work / "README.md").read_text()
        self.assertEqual(sum("median-eli5.html" in ln for ln in readme.splitlines()), 1)
        self.assertEqual(readme.count("## ELI5 explainers"), 1)

    def test_readme_line_goes_into_the_eli5_section_not_a_later_one(self):
        work = self.make_week()
        (work / "README.md").write_text(
            "# Week 3 Work\n\n## ELI5 explainers\n\n- [`old-eli5.html`](old-eli5.html) — old.\n\n"
            "## Practice exam\n\n- exam line\n")
        eli5_page.build(self.page, root=str(self.root))
        readme = (work / "README.md").read_text()
        eli5_part, exam_part = readme.split("## Practice exam")
        self.assertIn("median-eli5.html", eli5_part)
        self.assertNotIn("median-eli5.html", exam_part)
        self.assertIn("- exam line", exam_part)

    def test_week_must_match_exactly_one_folder(self):
        (self.root / "MA-235").mkdir()
        with self.assertRaises(ValueError):  # no Week-03 folder
            eli5_page.build(self.page, root=str(self.root))
        self.make_week()
        self.make_week(name="Week-03_copy")
        with self.assertRaises(ValueError):  # two Week-03 folders
            eli5_page.build(self.page, root=str(self.root))

    def test_refuses_to_replace_a_non_eli5_file(self):
        out = self.root / "median-eli5.html"
        out.write_text("my essay draft")
        with self.assertRaises(ValueError):
            eli5_page.build(self.page, out=str(out))
        self.assertEqual(out.read_text(), "my essay draft")

    def test_failing_page_writes_nothing(self):
        page = copy.deepcopy(self.page)
        page["steps"] = page["steps"][:1]  # checker needs at least two steps
        out = self.root / "bad-eli5.html"
        with self.assertRaises(ValueError):
            eli5_page.build(page, out=str(out))
        self.assertFalse(out.exists())

    def test_cli_out_mode(self):
        out = self.root / "cli-eli5.html"
        self.assertEqual(eli5_page.main([str(EXAMPLE), "--out", str(out)]), 0)
        self.assertEqual(eli5.check(out.read_text())[0], [])


if __name__ == "__main__":
    unittest.main()
