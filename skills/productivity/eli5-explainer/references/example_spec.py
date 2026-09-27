"""Minimal ELI5 spec. Build with:

  python3 scripts/eli5_page.py references/example_spec.py --out /tmp/median-eli5.html

Course topics add course/week/slug/blurb and build with --root <term folder>.
Colors: step cls s1..s5 and SVG classes k1..k5 map to one category each; keep them
consistent across steps. Box text on a colored fill uses tcls "on".
"""
from eli5_page import svg, box, text, arrow

PAGE = dict(
    course="MA-235", week=3, slug="median", title="The Median",
    blurb="picture-first walkthrough of finding a median.",
    tag="Example · explain it simply",
    h1="The middle value",
    lede="Sort the numbers, then take the one in the middle.",
    hero=svg(box(20, 20, 280, 60, "2  3  5  8  9", "card") + text(160, 110, "median = 5", "big"),
             "Five sorted numbers with the middle one, 5, marked.", "0 0 320 130"),
    steps=[
        dict(cls="s1", label="SORT", h2="<b>Sort</b> first",
             svg=svg(box(20, 30, 140, 50, "9 2 8 3 5", "card") + arrow(164, 55, 196, 55)
                     + box(200, 30, 140, 50, "2 3 5 8 9", "fill k1", "on"), "Unsorted numbers become sorted."),
             p=["Put the values in order before looking for the middle."]),
        dict(cls="s2", label="MIDDLE", h2="Take the <b>middle</b>",
             svg=svg(box(20, 30, 320, 50, "position (n + 1) ÷ 2 = 3 → 5", "fill k2", "on"), "The third of five values is the median."),
             p=["With n values, the middle position is (n + 1) ÷ 2."],
             analogy="like the person standing in the middle of a line."),
    ],
    recap=dict(h2="Sort, then middle",
               svg=svg(box(20, 30, 320, 50, "sort → middle", "card"), "Recap: sort, then take the middle.", "0 0 360 110")),
    footer=["Example spec for the eli5-explainer skill."],
)
