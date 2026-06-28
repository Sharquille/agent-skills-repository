#!/usr/bin/env python3
"""decorate_unl.py — add visual zone shapes and text labels to an EVE-NG Pro .unl.

Reads an existing .unl (nodes + networks already laid out) and injects
<textobject> elements for colored zone rectangles and IP/subnet/zone labels.
The running-config and node/network structure are not modified.

Usage:
  scripts/decorate_unl.py lab.unl decoration-spec.json -o lab.unl

Spec JSON:
  {
    "replace_textobjects": true,
    "shapes": [
      {"type":"square", "left":230, "top":410, "width":220, "height":170,
       "fill":[113,167,153,0.41], "stroke":[0,128,0,1], "dash":"10,10",
       "radius":18, "stroke_width":1.4}
    ],
    "labels": [
      {"left":240, "top":430, "text":"LAB / SUBJECT", "bold": true, "size":17},
      {"left":290, "top":540, "text":"10.10.70.10/24", "mono": true,
       "size":12, "width":180, "color":"#374151"}
    ]
  }

Shape types: "square" (rectangle with rounded corners) or "shape" (rectangle).
Color arrays are [r,g,b,a] floats in 0-255 (rgba). dash default is "10,10".
IDs are allocated starting above the maximum existing numeric id in the .unl.
"""

import argparse
import base64
import html
import json
import sys
import xml.etree.ElementTree as ET


def _next_id(root, start=1000):
    """Return an integer id safely above any existing numeric id."""
    ids = set()
    for elem in root.iter():
        val = elem.get("id")
        if val and val.isdigit():
            ids.add(int(val))
    return max(ids | {start - 1}) + 1


def _b64_html(html_doc: str) -> str:
    return base64.b64encode(html_doc.encode("utf-8")).decode("utf-8")


def _make_shape_textobject(shape_id, spec):
    left = int(spec["left"])
    top = int(spec["top"])
    width = int(spec["width"])
    height = int(spec["height"])
    r, g, b, a = spec["fill"]
    sr, sg, sb, sa = spec.get("stroke", [21, 21, 21, 1])
    dash = spec.get("dash", "10,10")
    radius = int(spec.get("radius", 18))
    stroke_width = spec.get("stroke_width", 1)
    name = spec.get("label", "")
    html_doc = (
        f'<div id="customShape{shape_id}" class="customShape context-menu resizable-content" '
        f'name="{html.escape(name, quote=True)}" style="display:inline; z-index:998; width:{width}px; height:{height}px; '
        f'visibility:visible; position:absolute; left:{left}px; top:{top}px;" '
        f'data-jtk-managed="customShape{shape_id}">\n'
        f'  <svg width="{width}px" height="{height}px">\n'
        f'    <rect x="2" y="2" width="{width - 2}px" height="{height - 2}px" rx="{radius}" ry="{radius}" '
        f'fill="rgba({r}, {g}, {b}, {a})" stroke="rgba({sr}, {sg}, {sb}, {sa})" '
        f'stroke-width="{stroke_width}" stroke-dasharray="{dash}"></rect>\n'
        '  </svg>\n'
        '</div>'
    )
    return shape_id, _b64_html(html_doc), name, "square"


def _make_label_textobject(label_id, spec):
    left = int(spec["left"])
    top = int(spec["top"])
    text = spec["text"]
    bold = spec.get("bold", False)
    name = spec.get("name", text[:32])
    safe_text = "<br/>".join(html.escape(str(text)).splitlines())
    inner = f"<strong>{safe_text}</strong>" if bold else safe_text
    font_size = int(spec.get("size", spec.get("font_size", 14)))
    color = spec.get("color", "#111827")
    family = "font-family:'Menlo','Consolas',monospace; " if spec.get("mono") else ""
    weight = "font-weight:700; " if bold else "font-weight:400; "
    width = f"width:{int(spec['width'])}px; " if spec.get("width") else "width:auto; "
    align = spec.get("align", "left")
    line_height = spec.get("line_height", 1.2)
    html_doc = (
        f'<div data-v-0e2f5934="" id="customText{label_id}" '
        f'class="customText customShape context-menu ck ck-content resizable-content" '
        f'name="{html.escape(name, quote=True)}" data-jtk-managed="customText{label_id}" '
        f'style="z-index:1000; cursor:move; display:inline; {width}height:auto; '
        f'visibility:visible; position:absolute; left:{left}px; top:{top}px; '
        f'{family}{weight}font-size:{font_size}px; line-height:{line_height}; '
        f'text-align:{align}; color:{color};">'
        f'<p>{inner}</p></div>'
    )
    return label_id, _b64_html(html_doc), name, "text"


def decorate(unl_path: str, spec_path: str, output_path: str):
    tree = ET.parse(unl_path)
    root = tree.getroot()
    spec = json.load(open(spec_path, encoding="utf-8"))

    objects = root.find("objects")
    if objects is None:
        objects = ET.SubElement(root, "objects")
    textobjects = objects.find("textobjects")
    if spec.get("replace_textobjects") and textobjects is not None:
        objects.remove(textobjects)
        textobjects = None
    if textobjects is None:
        configs = objects.find("configs")
        idx = list(objects).index(configs) if configs is not None else len(list(objects))
        textobjects = ET.Element("textobjects")
        objects.insert(idx, textobjects)

    next_id = _next_id(root)

    for shape in spec.get("shapes", []):
        sid, data, name, typ = _make_shape_textobject(next_id, shape)
        to = ET.SubElement(textobjects, "textobject", id=str(sid), name=name, type=typ)
        ET.SubElement(to, "data").text = data
        next_id += 1

    for label in spec.get("labels", []):
        lid, data, name, typ = _make_label_textobject(next_id, label)
        to = ET.SubElement(textobjects, "textobject", id=str(lid), name=name, type=typ)
        ET.SubElement(to, "data").text = data
        next_id += 1

    ET.indent(tree, space="  ", level=0)
    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=False)
    header = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    with open(output_path, "wb") as f:
        f.write(header.encode("utf-8"))
        f.write(xml_bytes)


def main():
    ap = argparse.ArgumentParser(description="Add visual zone shapes + labels to an EVE-NG Pro .unl")
    ap.add_argument("unl", help="input .unl file")
    ap.add_argument("spec", help="decoration spec JSON file")
    ap.add_argument("-o", "--output", help="output .unl file (default: overwrite input)")
    args = ap.parse_args()
    decorate(args.unl, args.spec, args.output or args.unl)
    print(f"Wrote {args.output or args.unl}")


if __name__ == "__main__":
    main()
