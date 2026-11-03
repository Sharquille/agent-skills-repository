import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eli5_page as ep  # noqa: E402


class LabelFitTest(unittest.TestCase):
    def setUp(self):
        ep.LABEL_WARNINGS.clear()

    def test_long_label_in_a_small_box_is_reported(self):
        ep.box(0, 0, 160, 30, "(c) the list order chose")
        self.assertEqual(len(ep.LABEL_WARNINGS), 1)
        self.assertIn("(c) the list order chose", ep.LABEL_WARNINGS[0])

    def test_fitting_labels_and_small_text_pass(self):
        ep.box(0, 0, 160, 30, "(c) list order chose")
        ep.box(0, 0, 150, 30, "a longer small caption", tcls="sm")
        self.assertEqual(ep.LABEL_WARNINGS, [])


class EdgeFitTest(unittest.TestCase):
    def setUp(self):
        ep.LABEL_WARNINGS.clear()

    def test_label_past_the_left_edge_is_reported(self):
        ep.svg(ep.text(36, 20, "median still 25", "sm", "end"), "a picture")
        self.assertEqual(len(ep.LABEL_WARNINGS), 1)
        self.assertIn("runs past the picture's edge", ep.LABEL_WARNINGS[0])

    def test_labels_inside_the_frame_pass(self):
        ep.svg(ep.text(180, 20, "centered caption", "sm") + ep.text(10, 40, "left label", "sm", "start"), "a picture")
        self.assertEqual(ep.LABEL_WARNINGS, [])



class BuilderRefusesClippedLabelsTest(unittest.TestCase):
    def test_script_run_fails_and_writes_nothing(self):
        # Run as a script: the spec's "from eli5_page import ..." must share the builder's warning list.
        import subprocess
        import sys
        import tempfile
        script = Path(__file__).resolve().parents[1] / "scripts" / "eli5_page.py"
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "spec.py"
            spec.write_text(
                "from eli5_page import svg, text\n"
                "PIC = svg(text(36, 20, 'median still 25', 'sm', 'end'), 'a picture')\n"
                "PAGE = dict(title='T', tag='t', h1='h', lede='l', hero=PIC, "
                "steps=[dict(cls='s1', label='A', h2='a', svg=PIC, p=['x']), dict(cls='s2', label='B', h2='b', svg=PIC, p=['y'])], "
                "recap=dict(h2='r', svg=PIC), footer=['f'])\n")
            out = Path(tmp) / "page.html"
            run = subprocess.run([sys.executable, str(script), str(spec), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("labels would be clipped", run.stdout)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
