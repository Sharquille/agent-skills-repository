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
# KaTeX typesets $...$ and $$...$$ in Core, the same syntax Obsidian renders. Pinned and
# integrity-checked like Mermaid; loaded only when a notebook has math.
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/"
KATEX_CSS_SRI = "sha384-3rdsX6e5mueWyoweR9NIVmtEsUkokpBT/0ALqKKIBMr9j4qhHkaIkAcGgsE6uVlp"
KATEX_JS_SRI = "sha384-QFFtAGzvvj+bfgCGxXJlNZZR1nXEZgvG8tDLCCY1F19xl20WlfTYgguB4VcNdxYk"
MATH_HEAD = (f'<link rel="stylesheet" href="{KATEX}katex.min.css" integrity="{KATEX_CSS_SRI}" crossorigin="anonymous">\n'
             f'<script src="{KATEX}katex.min.js" integrity="{KATEX_JS_SRI}" crossorigin="anonymous"></script>')
MATH_JS = """document.querySelectorAll(".tex").forEach(el => {
  try { // \\frac prints full height inline so fractions stay readable on the iPad.
        katex.render(el.dataset.tex, el, { displayMode: el.classList.contains("display"), throwOnError: true,
                                           macros: { "\\\\frac": "\\\\dfrac" } });
        el.dataset.ok = "1"; }
  catch (e) { el.classList.add("tex-error"); el.textContent = "TeX error: " + e.message; }
});"""
# Code is skipped; math follows pandoc's rule so `$C$1`, $5, "$5 and $10", and ($$) stay text.
MATH_OR_CODE = re.compile(
    r"(?P<code>```.*?```|`[^`\n]*`)"
    r"|\$\$(?!\))(?P<display>.+?)(?<!\()\$\$"  # not "($$)", a price marker
    r"|(?<![\\\w$])\$(?P<inline>[^\s$](?:[^$\n]*?[^\s$])?)\$(?![\w$])", re.S)
ACRONYMS = {"Https": "HTTPS", "Http": "HTTP", "Html": "HTML", "Css": "CSS",
            "Url": "URL", "Ip": "IP", "Lan": "LAN", "Io": "I/O"}
PLAIN_EDGE = re.compile(r"^\s*(\w+)\s*-->\s*(\w+)\s*$")
NODE_DEF = re.compile(r"^\s*(\w+)\s*[\(\[\{]")
SCRATCH_PAGES = 3
# Certification learners write in the margin and Practice.md, not on blank pads.
SCRATCH_BY_PROFILE = {"security": 0}
CORE_STOP = re.compile(r"(?i)^#\s+.*\b(quiz why|retrieval)\s*$")
RETRIEVAL_MAP_SUFFIXES = ("decision-flow", "error-flow")
# Homework bridge tools teach material the section does not earn; they stay on disk.
DISK_ONLY_MAP_SUFFIX = "bridge-tool"
NODE_ID = r"[A-Za-z][A-Za-z0-9_]*"
NODE_LINE = re.compile(rf"^\s*({NODE_ID})\s*[\(\[\{{>]")
EDGE_LINE = re.compile(
    rf"^\s*({NODE_ID})\b.*?(?:-->|-\.->|==>|---)\s*(?:\|[^|]*\|\s*)?({NODE_ID})\b")
CLASS_LINE = re.compile(r"^\s*class\s+([A-Za-z0-9_,\s]+?)\s+(\S+)\s*;?\s*$")
LINKSTYLE_LINE = re.compile(r"^\s*linkStyle\s+([\d,\s]+?)\s+(\S.*)$")
CHAPTER_HUB = re.compile(r"^CH(\d+)_\d+$")
# A GFM alert label line, any blank "> " lines after it, and the next line's "> "
# prefix, so the label opens the first paragraph instead of printing a literal ">".
# A figure is a Markdown image line pointing at an SVG beside the notes; Obsidian shows
# the same file, and the notebook inlines it.
FIGURE_LINE = validate_kit.FIGURE_LINE
# A margin prompt is a TIP callout whose body starts with **SKETCH:** or **RECALL:**.
CUE = re.compile(r"(?m)^>[ \t]?\[!TIP\][ \t]*\n>[ \t]?\*\*(SKETCH|RECALL):\*\*[ \t]*(.+)$")
TERMS_BOX = validate_kit.TERMS_BOX
HIGH_YIELD = validate_kit.HIGH_YIELD
RESEARCH_DATE = re.compile(r"(?m)^Research: (web|offline) \((\d{4}-\d{2}-\d{2})\)")
TERM_LINE = re.compile(r"^>[ \t]?- \*\*([^*]+)\*\*:?[ \t]*(.*)$")
MAP_SECTION = '<section class="map landscape">'
ORIENT = re.compile(r'data-map="(\d+)"[^>]*data-orient="(portrait|landscape)"')
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


def inline_figure(notes: Path, number: int, name: str) -> str:
    """The SVG beside the notes, ids namespaced so several figures share one page."""
    path = notes.parent / name
    if path.parent != notes.parent or not path.is_file():
        raise ValueError(f"{notes.parent.name}: figure {name} not found beside the notes")
    svg = path.read_text()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r'\bid="([^"]+)"', rf'id="f{number}-\1"', svg)
    svg = re.sub(r'(url\(#|href="#)([^)"]+)', rf"\g<1>f{number}-\2", svg)
    return f'\n<div class="fig">{svg}</div>\n'


def protect_math(text: str) -> tuple[str, list[tuple[str, bool]]]:
    """Swap math for placeholders so Markdown cannot mangle `_`, `*`, or `\\`."""
    found: list[tuple[str, bool]] = []

    def swap(m: re.Match) -> str:
        if m.group("code"):
            return m.group("code")
        display = m.group("display") is not None
        found.append(((m.group("display") if display else m.group("inline")).strip(), display))
        return f"@@MATH{len(found) - 1}@@"
    return MATH_OR_CODE.sub(swap, text), found


def restore_math(body: str, found: list[tuple[str, bool]]) -> str:
    def tag(i: int) -> str:
        tex, display = found[i]
        cls = "tex display" if display else "tex"
        el = "div" if display else "span"
        return f'<{el} class="{cls}" data-tex="{html.escape(tex, quote=True)}"></{el}>'
    body = re.sub(r"<p>@@MATH(\d+)@@</p>", lambda m: tag(int(m.group(1))), body)
    return re.sub(r"@@MATH(\d+)@@", lambda m: tag(int(m.group(1))), body)


def terms_html(lines: str) -> str:
    """A margin glossary box: each short form in bold, then what it means."""
    items = [TERM_LINE.match(line) for line in lines.strip().splitlines()]
    rows = "".join(f'<div class="term"><b>{html.escape(m.group(1))}</b> {html.escape(m.group(2))}</div>'
                   for m in items if m)
    return f'\n<div class="cue terms"><b>TERMS</b>{rows}</div>\n'


def core_html(notes: Path) -> str:
    """Core only (no Quiz why / Retrieval); each level-2 source section opens a page."""
    text = extract_core(notes.read_text())
    text = re.sub(r"^# .*\n", "", text, count=1)  # the cover carries the title
    counter = iter(range(1, 1000))
    text = FIGURE_LINE.sub(lambda m: inline_figure(notes, next(counter), m.group(2)), text)
    text = TERMS_BOX.sub(lambda m: terms_html(m.group(1)), text)
    text = HIGH_YIELD.sub(lambda m: f'\n<p class="hy"><b>HIGH YIELD</b> {html.escape(m.group(1).strip())}</p>\n',
                          text)
    text = CUE.sub(lambda m: f'\n<div class="cue"><b>{m.group(1)}</b>{html.escape(m.group(2).strip())}</div>\n',
                   text)
    text = GFM_ALERT.sub(lambda m: f"> **{m.group(1).upper()}:** ", text)
    text, found = protect_math(text)
    body = restore_math(markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"]), found)
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


def study_basis(kit: Path, hub: dict, state: dict) -> str:
    """What this notebook studies and how current it is, for the cover."""
    parts = [f"Studying {hub['exam']}" if hub.get("exam") else ""]
    parts.append(hub.get("study_basis", ""))
    if state.get("revised"):
        parts.append(f"notes revised {state['revised']}")
    relevance = kit / "relevance.md"
    checked = RESEARCH_DATE.search(relevance.read_text()) if relevance.is_file() else None
    if checked:
        parts.append(f"relevance checked {checked.group(2)} ({checked.group(1)})")
    return " · ".join(p for p in parts if p)


def section_html(section: str, folder: Path, course: str, week: int, title: str,
                 scratch: int = SCRATCH_PAGES, basis: str = "") -> tuple[str, int]:
    """Return the notebook HTML and how many Mermaid diagrams it holds."""
    notes = sorted(folder.glob("*Study-Notes.md"))
    if len(notes) != 1:
        raise ValueError(f"{folder}: need exactly one *Study-Notes.md")
    maps = sorted((p for p in folder.glob("*.mmd") if "overall" not in p.stem.lower()
                   and not p.stem.lower().endswith(DISK_ONLY_MAP_SUFFIX)), key=map_kind_rank)
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
    pages += [blank_page(f"Scratch {i}") for i in range(1, scratch + 1)]

    contents = [
        "Map: " + ", ".join(["concept map"] + [map_title(section, p) for p in legends]),
        "Notes: Core with a writing margin",
        "Retrieval: " + (", ".join(map_title(section, p) for p in sorts) or "none")
        + " (redraw first, then check)",
    ] + (["Scratch: blank pages for working out answers"] if scratch else [])
    cover = f"""<section class="cover portrait">
<p class="kicker">{html.escape(course)} · Week {week:02d} · GoodNotes notebook</p>
<h1>{html.escape(section_folder_name(section, title))}</h1>
{f'<p class="basis">{html.escape(basis)}</p>' if basis else ''}
<ol class="contents">{''.join(f'<li>{html.escape(c)}</li>' for c in contents)}</ol>
<div class="howto"><strong>First pass:</strong> Map → Notes → Practice.md in Obsidian.<br>
<strong>Return visits:</strong> start closed-book. Redraw a Retrieval map or answer Practice items before you look back.</div>
</section>"""
    return page(html.escape(title), cover + "".join(pages)), diagrams


def overview_html(kit: Path, course: str, scratch: int = SCRATCH_PAGES) -> tuple[str, int]:
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
    body = cover + "".join(pages) + (blank_page("Scratch 1") if scratch else "")
    return page("Course map", body), 1 + len(parts)


def page(title: str, body: str) -> str:
    math = 'class="tex' in body
    return PAGE.format(title=title, body=body, mermaid=MERMAID_JS, sri=MERMAID_SRI,
                       math_head=MATH_HEAD if math else "", math_js=MATH_JS if math else "")


def rendered_ok(dom: str, expected: int, math: int = 0) -> list[str]:
    """Problems in Chrome's dumped DOM; empty means every diagram and equation drew."""
    problems = []
    typeset = dom.count('data-ok="1"')
    if typeset != math:
        problems.append(f"{typeset} of {math} equations typeset")
    if re.search(r'class="[^"]*\btex-error', dom):  # the CSS and script also name the class
        problems.append("KaTeX reported an equation error")
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


def apply_orientation(page_html: str, dom: str) -> str:
    """Fix each map page's orientation before printing.

    Changing a page's orientation while Chrome prints makes it lay the portrait
    Core pages out at landscape width and shrink them, so the first pass records
    each map's shape and the print pass starts with the final classes.
    """
    orient = {int(n): o for n, o in ORIENT.findall(dom)}
    counter = iter(range(10**6))
    return re.sub(re.escape(MAP_SECTION),
                  lambda m: f'<section class="map {orient.get(next(counter), "landscape")}">', page_html)


def number_maps(page_html: str) -> str:
    counter = iter(range(10**6))
    return re.sub(re.escape(MAP_SECTION),
                  lambda m: f'<section class="map landscape" data-map="{next(counter)}">', page_html)


def render(page_html: str, expected: int, out: Path) -> None:
    if not CHROME.exists():
        raise FileNotFoundError(f"Google Chrome not found at {CHROME}")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "notebook.html"
        source.write_text(number_maps(page_html))
        # One retry: a slow jsDelivr fetch occasionally leaves every diagram undrawn.
        for _ in range(2):
            dom = chrome("--dump-dom", source.as_uri()).stdout
            problems = rendered_ok(dom, expected, page_html.count('class="tex'))
            if not problems:
                break
        if problems:
            raise RuntimeError(f"{out.name}: " + "; ".join(problems))
        source.write_text(apply_orientation(page_html, dom))
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
    hub = json.loads((kit / "hub.json").read_text())
    course = hub["goodnotes_course"]
    scratch = SCRATCH_BY_PROFILE.get(hub.get("profile"), SCRATCH_PAGES)
    built = []
    for section, folder in iter_sections(kit):
        if only and section != only:
            continue
        state = section_state(folder)
        week, title = state["week"], state["title"].strip()
        page_html, diagrams = section_html(section, folder, course, week, title, scratch,
                                           study_basis(kit, hub, state))
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
    page_html, diagrams = overview_html(kit, course, scratch)
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
section:last-of-type {{ break-after: auto; }}  /* the closing <script> is the last child */
.portrait {{ page: portraitpage; }}
.landscape {{ page: landscapepage; }}
.cover h1 {{ font-size: 30pt; color: var(--navy); margin: 0.2in 0 0.3in; }}
.basis {{ color: var(--muted); font-size: 10pt; margin: -0.15in 0 0.25in; }}
.kicker {{ color: var(--muted); letter-spacing: .04em; text-transform: uppercase; font-size: 9pt; margin-top: 1.2in; }}
.contents li {{ margin: 6pt 0; }}
.howto {{ margin-top: .4in; padding: 12pt 14pt; background: var(--tint); border-left: 4px solid var(--navy); }}
.maptitle {{ font-size: 12pt; color: var(--navy); margin: 0 0 8pt; }}
/* overflow:hidden stops Chrome shrinking every later page when a portrait map follows a landscape one */
.map {{ display:flex; flex-direction:column; overflow:hidden; }}
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
.notes .col > h2.section:first-of-type {{ break-before: auto; }}
h2.section {{ break-after: avoid; }}  /* never strand a section title at a page bottom */
.fig {{ margin: 6pt 0 8pt; break-inside: avoid; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }}
.cue {{ float: right; clear: right; width: 2.0in; margin: 2pt -2.28in 6pt 0; padding: 5pt 7pt; border: 1.2px dashed var(--navy);
  border-radius: 4pt; font-size: 8.5pt; line-height: 1.35; color: var(--navy); background: #fff; }}
.cue b {{ display: block; letter-spacing: .06em; font-size: 7.5pt; margin-bottom: 2pt; }}
p.hy {{ background: #FFF1B8; border-left: 4px solid #E0B000; padding: 3pt 7pt; border-radius: 2pt; font-size: 9.5pt;
  break-inside: avoid; break-after: avoid; }}
p.hy b {{ letter-spacing: .06em; font-size: 8pt; margin-right: 4pt; }}
.cue.terms {{ border-style: solid; border-width: 1px; background: var(--tint); color: var(--ink); }}
.cue.terms b {{ color: var(--navy); }}
.cue.terms .term {{ margin: 0 0 2.5pt; }}
.cue.terms .term b {{ display: inline; letter-spacing: 0; font-size: 8.5pt; margin: 0; }}
h3 {{ font-size: 11.5pt; margin: 14pt 0 3pt; break-after: avoid; }}
p {{ margin: 0 0 6pt; }}
p.test {{ background: var(--tint); padding: 4pt 7pt; border-radius: 3pt; break-inside: avoid; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 9.5pt; break-inside: avoid; }}
th, td {{ border: 1px solid var(--rule); padding: 3pt 5pt; text-align: left; vertical-align: top; }}
th {{ background: var(--tint); }}
code {{ font: 9pt Menlo, monospace; background: #F4F6F8; padding: 0 2pt; border-radius: 2pt; }}
pre:not(.mermaid) {{ background: #F4F6F8; padding: 6pt; white-space: pre-wrap; break-inside: avoid; }}
.edgeLabel, .edgeLabel p, .edgeLabel span, .edgeLabel div {{ color:#24313F !important; background:#FFFFFF !important; font-weight:600; }}
.tex.display {{ display: block; margin: 6pt 0 8pt; text-align: center; }}
/* full-height inline fractions need taller lines so stacked lines don't collide */
p:has(.mfrac), li:has(.mfrac), td:has(.mfrac) {{ line-height: 2.7; }}
li:has(.mfrac) {{ margin: 3pt 0; }}
.tex-error {{ color: #5C4023; }}
blockquote {{ margin: 6pt 0; padding: 6pt 10pt; border-left: 3px solid #6FA98A; background: #F3FAF6; break-inside: avoid; }}
</style>
{math_head}
<script src="{mermaid}" integrity="{sri}" crossorigin="anonymous"></script>
</head><body>
{body}
<script>
mermaid.initialize({{ startOnLoad: false, theme: "base", flowchart: {{ htmlLabels: true, useMaxWidth: true }},
  themeVariables: {{ fontFamily: "-apple-system, Helvetica Neue, Arial, sans-serif", fontSize: "15px",
  edgeLabelBackground: "#FFFFFF" }} }});
{math_js}
mermaid.run().then(() => {{
  // Tall drawings get a portrait page so their labels stay large. The first pass
  // records the shape; the builder sets the class before the print pass.
  document.querySelectorAll("section.map").forEach(sec => {{
    const svg = sec.querySelector("svg"); if (!svg) return;
    const box = svg.viewBox.baseVal;
    sec.dataset.orient = box && box.height > box.width * 0.9 ? "portrait" : "landscape";
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
