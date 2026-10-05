#!/usr/bin/env python3
"""Build one GoodNotes notebook PDF per kit section, plus a course-map notebook.

Each ready section becomes a single PDF in its week's Work/ folder: cover,
map pages (a large concept map also gets one page per section hub), Core
notes with a writing margin, redraw-then-check Retrieval pages, and scratch
pages. One AirDrop per section, filed once in GoodNotes.

Chrome renders the page twice: once to dump the DOM so a Mermaid failure
stops the build, then to print. A pinned, integrity-checked Mermaid loads from
jsDelivr, so a build needs a network connection; studying the PDF does not.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import validate_kit

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js"
# Subresource Integrity: Chrome refuses the script if jsDelivr ever serves other bytes.
# Bump the version and this hash together (see references/maintaining.md).
MERMAID_SRI = "sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2"
ACRONYMS = {"Https": "HTTPS", "Http": "HTTP", "Html": "HTML", "Css": "CSS",
            "Url": "URL", "Ip": "IP", "Lan": "LAN", "Io": "I/O"}
PLAIN_EDGE = re.compile(r"^\s*(\w+)\s*-->\s*(\w+)\s*$")
NODE_DEF = re.compile(r"^\s*(\w+)\s*[\(\[\{]")
SCRATCH_PAGES = 3
CORE_STOP = re.compile(r"(?i)^#\s+.*\b(quiz why|retrieval)\s*$")
RETRIEVAL_MAP_SUFFIXES = ("decision-flow", "error-flow")
NODE_ID = r"[A-Za-z][A-Za-z0-9_]*"
NODE_LINE = re.compile(rf"^\s*({NODE_ID})\s*[\(\[\{{>]")
EDGE_LINE = re.compile(
    rf"^\s*({NODE_ID})\b.*?(?:-->|-\.->|==>|---)\s*(?:\|[^|]*\|\s*)?({NODE_ID})\b")
CLASS_LINE = re.compile(r"^\s*class\s+([A-Za-z0-9_,\s]+?)\s+(\S+)\s*;?\s*$")
LINKSTYLE_LINE = re.compile(r"^\s*linkStyle\s+([\d,\s]+?)\s+(\S.*)$")
CHAPTER_HUB = re.compile(r"^CH(\d+)_\d+$")
# A GFM alert label line, any blank "> " lines after it, and the next line's "> "
# prefix, so the label opens the first paragraph instead of printing a literal ">".
GFM_ALERT = re.compile(
    r"(?im)^>[ \t]?\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*(?:\n(?:>[ \t]*\n)*>[ \t]?)?")


def numeric_key(name: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", name)
    return tuple(int(p) for p in parts) if parts else (10**9,)


def iter_sections(kit: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for chapter in sorted(kit.glob("Chapter-*"), key=lambda p: numeric_key(p.name)):
        if not chapter.is_dir():
            continue
        for section in sorted(chapter.iterdir(), key=lambda p: numeric_key(p.name)):
            if section.is_dir() and re.match(r"^\d+(\.\d+)*$", section.name):
                found.append((section.name, section))
    return found


def section_folder_name(section: str, title: str) -> str:
    """`3.2 Measures of Variation`; never `1.1 1.1` when the title is missing."""
    title = title.strip()
    if not title or title == section:
        return section
    if title.startswith(section + " "):
        return title
    return f"{section} {title}"


def section_state(folder: Path) -> dict:
    """state.json, already shape-checked by the kit contract; refuses an unreleased batch."""
    state = json.loads((folder / "state.json").read_text())
    if state["status"] not in {"ready", "complete"}:
        raise ValueError(f"{folder.name}: {state['status']}; wait for the batch to be released")
    return state


def map_kind_rank(path: Path) -> tuple[int, str]:
    stem = path.stem.lower()
    if stem.endswith("concept-map"):
        return (0, stem)
    if retrieval_map(path):
        return (1, stem)
    return (2, stem)


def retrieval_map(path: Path) -> bool:
    stem = path.stem.lower()
    return stem.endswith(RETRIEVAL_MAP_SUFFIXES) or "quiz-sort" in stem


def map_title(section: str, path: Path) -> str:
    """`it-4.1-https-flow.mmd` -> `HTTPS`; course tag and section number dropped."""
    lower = path.stem.lower()
    if lower.endswith("concept-map"):
        return "Concept Map"
    if lower.endswith("decision-flow"):
        return "Quiz Sort"
    rest = re.sub(rf"^(?:[a-z]+-)?{re.escape(section)}-", "", path.stem, flags=re.I)
    rest = re.sub(r"-?flow$", "", rest, flags=re.I)
    words = rest.replace("-", " ").strip().title().split() or [path.stem]
    title = " ".join(ACRONYMS.get(word, word) for word in words)
    return f"{title} Sort" if lower.endswith("error-flow") else title


def extract_core(text: str) -> str:
    """Keep Core; drop Quiz why and Retrieval prose from GoodNotes imports."""
    collected: list[str] = []
    for line in text.splitlines(keepends=True):
        if CORE_STOP.match(line.rstrip("\n")):
            break
        collected.append(line)
    core = "".join(collected).strip()
    if not core:
        raise ValueError("notes have no Core before Quiz why / Retrieval")
    return core + "\n"


def split_overall(code: str) -> list[tuple[int, str]]:
    """Split an oversized overall map into one course map per chapter.

    Each part keeps the root, that chapter's section hubs, everything reachable
    below them, shared class definitions, and restyled edges. Root-level nodes
    that belong to no chapter stay with the first part. Refuses to drop content.
    """
    header, class_defs, nodes, edges, classes, styles = None, [], {}, [], [], {}
    for line in code.splitlines():
        text = line.strip()
        if not text or text.startswith("%%"):
            continue
        if text.startswith(("flowchart ", "graph ")) and header is None:
            header = line
        elif text.startswith("classDef "):
            class_defs.append(line)
        elif (match := LINKSTYLE_LINE.match(line)):
            for index in re.findall(r"\d+", match.group(1)):
                styles[int(index)] = match.group(2)
        elif (match := CLASS_LINE.match(line)):
            classes.append(([i for i in re.split(r"[\s,]+", match.group(1)) if i], match.group(2)))
        elif (match := EDGE_LINE.match(line)):
            edges.append((match.group(1), match.group(2), line))
        elif (match := NODE_LINE.match(line)):
            nodes.setdefault(match.group(1), line)
        else:
            raise ValueError(f"Overall Map cannot be split automatically at: {text}")
    if header is None:
        raise ValueError("Overall Map has no flowchart header")
    order = list(nodes)
    for src, dst, _ in edges:
        for node in (src, dst):
            if node not in order:
                order.append(node)
    hubs: dict[int, list[str]] = {}
    for node in order:
        match = CHAPTER_HUB.match(node)
        if match:
            hubs.setdefault(int(match.group(1)), []).append(node)
    if len(hubs) < 2:
        raise ValueError("Overall Map is too long and has fewer than two chapters to split")
    root = order[0]
    children: dict[str, list[str]] = {}
    for src, dst, _ in edges:
        children.setdefault(src, []).append(dst)

    def reach(starts: list[str], blocked: set[str]) -> set[str]:
        seen, stack = set(), list(starts)
        while stack:
            node = stack.pop()
            if node in seen or node in blocked:
                continue
            seen.add(node)
            stack.extend(children.get(node, []))
        return seen

    every_hub = {hub for group in hubs.values() for hub in group}
    loose = reach([root], every_hub) - {root}
    parts, covered_nodes, covered_edges = [], set(), set()
    for number, chapter in enumerate(sorted(hubs)):
        keep = {root} | reach(hubs[chapter], {root} | (every_hub - set(hubs[chapter])))
        if number == 0:
            keep |= loose
        lines = [header, *class_defs]
        lines += [nodes[node] for node in order if node in keep and node in nodes]
        kept_edges = []
        for index, (src, dst, line) in enumerate(edges):
            if src in keep and dst in keep:
                kept_edges.append(index)
                lines.append(line)
        for ids, name in classes:
            present = [node for node in ids if node in keep]
            if present:
                lines.append(f"  class {','.join(present)} {name}")
        restyled: dict[str, list[str]] = {}
        for new_index, old_index in enumerate(kept_edges):
            if old_index in styles:
                restyled.setdefault(styles[old_index], []).append(str(new_index))
        lines += [f"  linkStyle {','.join(ids)} {style}" for style, ids in restyled.items()]
        parts.append((chapter, "\n".join(lines) + "\n"))
        covered_nodes |= keep
        covered_edges |= set(kept_edges)
    if set(order) - covered_nodes or len(covered_edges) != len(edges):
        raise ValueError("Overall Map split would drop nodes or edges; simplify labels instead")
    return parts


def split_concept(code: str) -> list[tuple[str, str]]:
    """One LR page per hub (root -> hub -> leaves) for a concept map too tall to read.

    Small maps, labelled edges, or any arrow this parser does not understand
    return [] so the whole map prints as drawn instead of being guessed at.
    """
    lines = code.splitlines()
    edges = []
    for line in lines:
        if "-->" in line or "-.->" in line:
            match = PLAIN_EDGE.match(line)
            if not match:
                return []
            edges.append((match.group(1), match.group(2)))
    if not edges:
        return []
    root = edges[0][0]
    hubs = [b for a, b in edges if a == root]
    if len(hubs) < 4 or len(edges) < 20:
        return []
    defs = {m.group(1): line for line in lines if (m := NODE_DEF.match(line))}
    styles = [line for line in lines if line.strip().startswith("classDef")]
    pages = []
    for node in hubs:
        leaves = [b for a, b in edges if a == node]
        label = re.search(r'"([^"]+)"', defs.get(node, f'"{node}"'))
        body = ["flowchart LR"] + [defs[n] for n in [root, node, *leaves] if n in defs]
        body += [f"  {root} --> {node}"] + [f"  {node} --> {leaf}" for leaf in leaves]
        body += styles + [f"  class {root} root", f"  class {node} hubV"]
        if leaves:
            body.append(f"  class {','.join(leaves)} leafV")
        pages.append((label.group(1).replace("<br/>", " ") if label else node, "\n".join(body)))
    return pages


def core_html(notes: Path) -> str:
    """Core only (no Quiz why / Retrieval); each level-2 source section opens a page."""
    text = extract_core(notes.read_text())
    text = re.sub(r"^# .*\n", "", text, count=1)  # the cover carries the title
    text = GFM_ALERT.sub(lambda m: f"> **{m.group(1).upper()}:** ", text)
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = body.replace("<p><strong>TEST MOVE:</strong>", '<p class="test"><strong>TEST MOVE:</strong>')
    return body.replace("<h2>", '<h2 class="section">')


def mermaid(code: str) -> str:
    return f'<pre class="mermaid">{html.escape(code)}</pre>'


def map_page(heading: str, code: str) -> str:
    return (f'<section class="map landscape"><h2 class="maptitle">{html.escape(heading)}</h2>'
            f"{mermaid(code)}</section>")


def blank_page(heading: str, hint: str = "", orientation: str = "portrait") -> str:
    note = f'<p class="hint">{html.escape(hint)}</p>' if hint else ""
    return (f'<section class="blank {orientation}"><h2 class="maptitle">{html.escape(heading)}</h2>'
            f"{note}</section>")


def section_html(section: str, folder: Path, course: str, week: int, title: str) -> tuple[str, int]:
    """Return the notebook HTML and how many Mermaid diagrams it holds."""
    notes = sorted(folder.glob("*Study-Notes.md"))
    if len(notes) != 1:
        raise ValueError(f"{folder}: need exactly one *Study-Notes.md")
    maps = sorted((p for p in folder.glob("*.mmd") if "overall" not in p.stem.lower()), key=map_kind_rank)
    concept = [p for p in maps if p.stem.lower().endswith("concept-map")]
    sorts = [p for p in maps if retrieval_map(p)]
    legends = [p for p in maps if p not in concept and p not in sorts]

    pages, diagrams = [], 0
    for path in concept:
        code = path.read_text()
        parts = split_concept(code)
        pages.append(map_page("Map · Overview" if parts else "Map · Concept Map", code))
        pages += [map_page(f"Map · {label}", part) for label, part in parts]
        diagrams += 1 + len(parts)
    for path in legends:
        pages.append(map_page(f"Map · {map_title(section, path)}", path.read_text()))
        diagrams += 1
    pages.append(f'<section class="notes portrait"><div class="col">{core_html(notes[0])}</div></section>')
    for path in sorts:
        name = map_title(section, path)
        pages.append(blank_page(f"Retrieval · {name}: redraw from memory",
                                "Close your notes. Draw the sort tree here, then turn the page to check.",
                                "landscape"))
        pages.append(map_page(f"Retrieval · {name}: check", path.read_text()))
        diagrams += 1
    pages += [blank_page(f"Scratch {i}") for i in range(1, SCRATCH_PAGES + 1)]

    contents = [
        "Map: " + ", ".join(["concept map"] + [map_title(section, p) for p in legends]),
        "Notes: Core with a writing margin",
        "Retrieval: " + (", ".join(map_title(section, p) for p in sorts) or "none")
        + " (redraw first, then check)",
        "Scratch: blank pages for working out answers",
    ]
    cover = f"""<section class="cover portrait">
<p class="kicker">{html.escape(course)} · Week {week:02d} · GoodNotes notebook</p>
<h1>{html.escape(section_folder_name(section, title))}</h1>
<ol class="contents">{''.join(f'<li>{html.escape(c)}</li>' for c in contents)}</ol>
<div class="howto"><strong>First pass:</strong> Map → Notes → Practice.md in Obsidian.<br>
<strong>Return visits:</strong> start closed-book. Redraw a Retrieval map or answer Practice items before you look back.</div>
</section>"""
    return PAGE.format(title=html.escape(title), body=cover + "".join(pages),
                       mermaid=MERMAID_JS, sri=MERMAID_SRI), diagrams


def overview_html(kit: Path, course: str) -> tuple[str, int]:
    """Course notebook for 00 Course Overview: whole overall map, then one page per chapter."""
    code = (kit / "overall-flow.mmd").read_text()
    try:
        parts = split_overall(code)
    except ValueError:  # one chapter so far, or syntax the splitter refuses to guess at
        parts = []
    pages = [map_page("Overall map", code)]
    pages += [map_page(f"Overall map · Chapter {chapter}", part) for chapter, part in parts]
    cover = f"""<section class="cover portrait">
<p class="kicker">{html.escape(course)} · 00 Course Overview · GoodNotes notebook</p>
<h1>Course map</h1>
<div class="howto">Every section studied so far, grown from its sources. Redraw a chapter branch from memory, then check it here.</div>
</section>"""
    body = cover + "".join(pages) + blank_page("Scratch 1")
    return PAGE.format(title="Course map", body=body, mermaid=MERMAID_JS, sri=MERMAID_SRI), 1 + len(parts)


def rendered_ok(dom: str, expected: int) -> list[str]:
    """Problems in Chrome's dumped DOM; empty means every diagram drew."""
    problems = []
    drawn = dom.count('data-processed="true"')
    if drawn != expected:
        problems.append(f"{drawn} of {expected} Mermaid diagrams rendered")
    if "Syntax error in text" in dom:
        problems.append("Mermaid reported a syntax error")
    if "<title>READY</title>" not in dom:
        problems.append("page did not finish rendering")
    return problems


def chrome(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                           "--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw",
                           *args], check=True, capture_output=True, text=True, timeout=180)


def render(page_html: str, expected: int, out: Path) -> None:
    if not CHROME.exists():
        raise FileNotFoundError(f"Google Chrome not found at {CHROME}")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "notebook.html"
        source.write_text(page_html)
        # One retry: a slow jsDelivr fetch occasionally leaves every diagram undrawn.
        for _ in range(2):
            problems = rendered_ok(chrome("--dump-dom", source.as_uri()).stdout, expected)
            if not problems:
                break
        if problems:
            raise RuntimeError(f"{out.name}: " + "; ".join(problems))
        pending = out.with_name(out.stem + ".pending.pdf")
        chrome(f"--print-to-pdf={pending}", source.as_uri())
        pending.replace(out)


def week_work(course: Path, week: int) -> Path:
    """Week-04_... or Weeks-14-15_... folder holding this week; its Work/ gets the PDF."""
    for folder in sorted(course.glob("Week*")):
        match = re.match(r"^Weeks?-(\d+)(?:-(\d+))?_", folder.name)
        if match and int(match.group(1)) <= week <= int(match.group(2) or match.group(1)):
            return folder / "Work"
    raise FileNotFoundError(f"{course.name}: no week folder for week {week}")


def pdf_name(course: Path, section: str, title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-") or "Notes"
    return f"{course.name}_{section}_{slug}_GoodNotes.pdf"


def build(kit: Path, only: str | None, downloads: bool) -> list[Path]:
    kit = kit.resolve()
    errors = validate_kit.check_kit(kit)
    if errors:
        raise ValueError("kit contract failed; run validate_kit.py --kit:\n  " + "\n  ".join(errors))
    course = json.loads((kit / "hub.json").read_text())["goodnotes_course"]
    built = []
    for section, folder in iter_sections(kit):
        if only and section != only:
            continue
        state = section_state(folder)
        week, title = state["week"], state["title"].strip()
        page_html, diagrams = section_html(section, folder, course, week, title)
        work = week_work(kit.parent, week)
        work.mkdir(parents=True, exist_ok=True)
        out = work / pdf_name(kit.parent, section, title)
        render(page_html, diagrams, out)
        if downloads:
            shutil.copy2(out, Path.home() / "Downloads" / out.name)
        print(f"{section:<6} {diagrams:>2} diagrams  {out.relative_to(kit.parent)}")
        built.append(out)
    if only and not built:
        raise ValueError(f"no section {only} in {kit}")
    # The overall map changes with every section, so its notebook is always rebuilt.
    page_html, diagrams = overview_html(kit, course)
    out = kit.parent / "00-Course-Guide" / f"{kit.parent.name}_Course-Overview_GoodNotes.pdf"
    out.parent.mkdir(exist_ok=True)
    render(page_html, diagrams, out)
    if downloads:
        shutil.copy2(out, Path.home() / "Downloads" / out.name)
    print(f"{'course':<6} {diagrams:>2} diagrams  {out.relative_to(kit.parent)}")
    return built + [out]


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>
@page portraitpage {{ size: Letter portrait; margin: 0.55in; }}
@page landscapepage {{ size: Letter landscape; margin: 0.45in; }}
:root {{ --ink:#1F2933; --navy:#1F3A5F; --muted:#5B6B7A; --rule:#C9D3DD; --tint:#EEF3F8; --margin:2.3in; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; color:var(--ink); background:#fff; font: 11pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; }}
section {{ break-after: page; }}
section:last-child {{ break-after: auto; }}
.portrait {{ page: portraitpage; }}
.landscape {{ page: landscapepage; }}
.cover h1 {{ font-size: 30pt; color: var(--navy); margin: 0.2in 0 0.3in; }}
.kicker {{ color: var(--muted); letter-spacing: .04em; text-transform: uppercase; font-size: 9pt; margin-top: 1.2in; }}
.contents li {{ margin: 6pt 0; }}
.howto {{ margin-top: .4in; padding: 12pt 14pt; background: var(--tint); border-left: 4px solid var(--navy); }}
.maptitle {{ font-size: 12pt; color: var(--navy); margin: 0 0 8pt; }}
.map {{ display:flex; flex-direction:column; }}
.map.landscape {{ height: 7.55in; }}
.map.portrait {{ height: 9.85in; }}
.map pre.mermaid {{ flex:1; min-height:0; margin:0; }}
.map svg {{ width:100% !important; height:100% !important; max-width:none !important; }}
.blank {{ min-height: 7in; }}
.blank.portrait {{ min-height: 9.6in; }}
.hint {{ color: var(--muted); font-size: 10pt; }}
.notes .col {{ margin-right: var(--margin); }}
.notes {{ background: linear-gradient(to left, transparent calc(var(--margin) - 0.12in), var(--rule) calc(var(--margin) - 0.12in),
  var(--rule) calc(var(--margin) - 0.1in), transparent calc(var(--margin) - 0.1in)); }}
h2.section {{ break-before: page; font-size: 15pt; color: var(--navy); border-bottom: 2px solid var(--navy); padding-bottom: 3pt; margin: 0 0 8pt; }}
.notes .col > h2.section:first-child {{ break-before: auto; }}
h3 {{ font-size: 11.5pt; margin: 14pt 0 3pt; break-after: avoid; }}
p {{ margin: 0 0 6pt; }}
p.test {{ background: var(--tint); padding: 4pt 7pt; border-radius: 3pt; break-inside: avoid; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 9.5pt; break-inside: avoid; }}
th, td {{ border: 1px solid var(--rule); padding: 3pt 5pt; text-align: left; vertical-align: top; }}
th {{ background: var(--tint); }}
code {{ font: 9pt Menlo, monospace; background: #F4F6F8; padding: 0 2pt; border-radius: 2pt; }}
pre:not(.mermaid) {{ background: #F4F6F8; padding: 6pt; white-space: pre-wrap; break-inside: avoid; }}
.edgeLabel, .edgeLabel p, .edgeLabel span, .edgeLabel div {{ color:#24313F !important; background:#FFFFFF !important; font-weight:600; }}
blockquote {{ margin: 6pt 0; padding: 6pt 10pt; border-left: 3px solid #6FA98A; background: #F3FAF6; break-inside: avoid; }}
</style>
<script src="{mermaid}" integrity="{sri}" crossorigin="anonymous"></script>
</head><body>
{body}
<script>
mermaid.initialize({{ startOnLoad: false, theme: "base", flowchart: {{ htmlLabels: true, useMaxWidth: true }},
  themeVariables: {{ fontFamily: "-apple-system, Helvetica Neue, Arial, sans-serif", fontSize: "15px",
  edgeLabelBackground: "#FFFFFF" }} }});
mermaid.run().then(() => {{
  // Tall drawings get a portrait page so their labels stay large.
  document.querySelectorAll("section.map").forEach(sec => {{
    const svg = sec.querySelector("svg"); if (!svg) return;
    const box = svg.viewBox.baseVal;
    if (box && box.height > box.width * 0.9) {{ sec.classList.replace("landscape", "portrait"); }}
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  }});
  document.title = "READY";
}});
</script>
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one GoodNotes notebook PDF per kit section.")
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--section", help="build one section, e.g. 4.1")
    parser.add_argument("--downloads", action="store_true", help="also copy each PDF to ~/Downloads")
    args = parser.parse_args()
    build(args.kit, args.section, args.downloads)


if __name__ == "__main__":
    main()
