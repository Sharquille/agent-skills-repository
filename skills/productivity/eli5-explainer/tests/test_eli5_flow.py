import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eli5  # noqa: E402
import eli5_flow  # noqa: E402
import eli5_page  # noqa: E402


def sampling_tree():
    leaf = lambda *lines: dict(text=list(lines), cls="fill k1", tcls="on")
    return dict(text=["How are items picked?"], children=[
        dict(text=["Convenience"], edge="a person decides", cls="fill k4", tcls="on"),
        dict(text=["Chance"], edge="a random process", band="Chance", band_cls="k3", children=[
            dict(text=["No grouping"], band="No grouping", children=[leaf("Simple random"), leaf("Systematic")]),
            dict(text=["Grouping first"], band="Grouping", band_cls="k5", children=[leaf("Stratified"), leaf("Cluster")]),
        ]),
    ])


def nodes_by_depth(n, depth=0, out=None):
    out = {} if out is None else out
    out.setdefault(depth, []).append(n)
    for c in n.get("children", []):
        nodes_by_depth(c, depth + 1, out)
    return out


class FlowTest(unittest.TestCase):
    def setUp(self):
        self.root = sampling_tree()
        self.svg = eli5_flow.tree(self.root, "Sampling methods by how items are picked.")

    def test_siblings_never_overlap_and_parents_are_centered(self):
        for depth, row in nodes_by_depth(self.root).items():
            row = sorted(row, key=lambda n: n["_x"])
            for a, b in zip(row, row[1:]):
                self.assertLessEqual(a["_x"] + a["_w"], b["_x"], f"overlap at depth {depth}")
        chance = self.root["children"][1]
        kids = chance["children"]
        self.assertAlmostEqual(chance["_cx"], (kids[0]["_cx"] + kids[-1]["_cx"]) / 2)

    def test_bands_enclose_their_subtrees(self):
        def check(n):
            for c in n.get("children", []):
                if n.get("band"):
                    self.assertGreaterEqual(c["_left"], n["_left"])
                    self.assertLessEqual(c["_right"], n["_right"])
                check(c)
        check(self.root)
        self.assertEqual(len(re.findall(r'class="soft k\d"', self.svg)), 3)
        for caption in ("Chance", "No grouping", "Grouping"):
            self.assertIn(f">{caption}</text>", self.svg)

    def test_edge_labels_and_checker(self):
        self.assertIn("a person decides", self.svg)
        page = eli5_page.render(dict(title="Flow", tag="t", h1="h", lede="l", hero=self.svg,
                                     steps=[dict(label="A", h2="a", svg=self.svg, p=["x"]),
                                            dict(label="B", h2="b", svg=self.svg, p=["y"])],
                                     recap=dict(h2="r", svg=self.svg), footer=["f"]))
        self.assertEqual(eli5.check(page)[0], [])


if __name__ == "__main__":
    unittest.main()
