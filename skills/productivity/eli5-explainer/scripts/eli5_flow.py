"""Decision trees and taxonomies for ELI5 pages, laid out automatically.

Use it only when the picture is a classification ("which kind is this?") or a
branching decision. Describe the tree; the layout places every node, keeps
siblings from overlapping, centers each parent over its children, and draws a
labeled band around any group that shares a boundary (for example "Grouping"
around stratified and cluster).

    from eli5_flow import tree
    pic = tree(dict(text=["How are items picked?"], children=[
        dict(text=["Convenience"], edge="a person decides", cls="fill k4", tcls="on"),
        dict(text=["Chance"], edge="a random process", band="Chance", band_cls="k3", children=[...]),
    ]), "Alt text describing the whole tree.")

Node keys: text (list of lines), cls ("card" or "fill kN"), tcls ("on" for text on
a colored fill), edge (label on the edge into this node), band (caption for a
band around this node and everything under it), band_cls ("k1".."k5"),
children. Borrowed from archify's rules: group only real boundaries, keep the
path flowing one way, never cross a node with an edge. Standard library only.
"""
from eli5_page import arrow, box, svg, text

CHAR_W = 7.2   # approximate width of one 13px, weight-600 character
LINE_H = 16
PAD = 10       # band padding
CAPTION = 18   # room for a band caption above its top node


def _measure(n):
    lines = n["text"]
    n["_w"] = max(84, round(max(len(line) for line in lines) * CHAR_W) + 20)
    n["_h"] = LINE_H * len(lines) + 16
    for c in n.get("children", []):
        _measure(c)
    kids = n.get("children", [])
    span = sum(c["_sw"] for c in kids) + n.get("_gap", 0) * max(0, len(kids) - 1)
    n["_sw"] = max(n["_w"], span) + (2 * PAD if n.get("band") else 0)


def _gap(n, gap_x):
    n["_gap"] = gap_x
    for c in n.get("children", []):
        _gap(c, gap_x)


def _levels(n, depth, heights):
    heights[depth] = max(heights.get(depth, 0), n["_h"])
    for c in n.get("children", []):
        _levels(c, depth + 1, heights)


def _place(n, left, depth, ys):
    inner = left + (PAD if n.get("band") else 0)
    width = n["_sw"] - (2 * PAD if n.get("band") else 0)
    kids = n.get("children", [])
    if kids:
        span = sum(c["_sw"] for c in kids) + n["_gap"] * (len(kids) - 1)
        x = inner + (width - span) / 2
        for c in kids:
            _place(c, x, depth + 1, ys)
            x += c["_sw"] + n["_gap"]
        n["_cx"] = (kids[0]["_cx"] + kids[-1]["_cx"]) / 2
    else:
        n["_cx"] = inner + width / 2
    n["_x"] = n["_cx"] - n["_w"] / 2
    n["_y"] = ys[depth]
    n["_left"], n["_right"] = left, left + n["_sw"]


def _bottom(n):
    return max([n["_y"] + n["_h"]] + [_bottom(c) for c in n.get("children", [])])


def _draw(n, bands, edges, nodes, parent_cx=None):
    if n.get("band"):
        top = n["_y"] - CAPTION - 8
        # Put the caption on the side away from the incoming edge so the edge never crosses it.
        left_side = parent_cx is None or parent_cx >= n["_cx"]
        cap_x = n["_left"] + 10 if left_side else n["_right"] - 10
        bands.append(f'<rect class="soft {n.get("band_cls", "k1")}" x="{n["_left"]:.1f}" y="{top:.1f}" '
                     f'width="{n["_sw"]:.1f}" height="{_bottom(n) + PAD - top:.1f}" rx="12"/>'
                     + text(round(cap_x, 1), round(top + 15, 1), n["band"], "sm", "start" if left_side else "end"))
    nodes.append(box(round(n["_x"], 1), n["_y"], n["_w"], n["_h"], n["text"], n.get("cls", "card"), n.get("tcls", "")))
    for c in n.get("children", []):
        x1, y1 = round(n["_cx"], 1), n["_y"] + n["_h"]
        x2, y2 = round(c["_cx"], 1), c["_y"] - 2
        edges.append(arrow(x1, y1, x2, y2))
        if c.get("edge"):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            side = "start" if x2 >= x1 else "end"
            edges.append(text(round(mx + (6 if side == "start" else -6), 1), round(my, 1), c["edge"], "sm", side))
        _draw(c, bands, edges, nodes, n["_cx"])


def tree(root, label, gap_x=18, gap_y=48, margin=8):
    """Return an inline SVG (role=img, aria-label=label) for the tree."""
    _gap(root, gap_x)
    _measure(root)
    heights = {}
    _levels(root, 0, heights)
    ys, y = {}, margin + CAPTION + 8
    for d in sorted(heights):
        ys[d] = y
        y += heights[d] + gap_y + CAPTION
    _place(root, margin, 0, ys)
    bands, edges, nodes = [], [], []
    _draw(root, bands, edges, nodes)
    width = root["_sw"] + 2 * margin
    height = _bottom(root) + PAD + margin + 4
    return svg("".join(bands + edges + nodes), label, f"0 0 {width:.0f} {height:.0f}")
