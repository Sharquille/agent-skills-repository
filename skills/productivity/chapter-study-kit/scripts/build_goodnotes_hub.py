#!/usr/bin/env python3
"""Build the GoodNotes hub HTML from Chapter-Kits sources. Verify claim URLs.

Discovers maps and note splits under Chapter-NN/<section>/ so a new section
does not require editing this file.
"""

from __future__ import annotations

import argparse
import base64
import html
import hashlib
import json
import re
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import validate_kit

CLAIM = "https://web.goodnotes.com/claim"
UA = {"User-Agent": "Mozilla/5.0"}
MAX_URL_CHARS = 7600
BTN = ("green", "amber", "plum", "alt")
NOTE_SPLIT_SUFFIXES = (
    ("Notes-Core.md", "Notes Core"),
    ("Notes-Quiz.md", "Quiz Why"),
    ("Notes-Retrieval.md", "Retrieval"),
)
CORE_STOP = re.compile(r"(?i)^#\s+.*\b(quiz why|retrieval)\s*$")
RETRIEVAL_MAP_SUFFIXES = ("decision-flow", "error-flow")


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode()


def strip_alerts(text: str) -> str:
    return re.sub(
        r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n",
        "",
        text,
        flags=re.M,
    ).strip()


def mermaid_url(code: str, title: str) -> str:
    params = {
        "source": "chatgpt",
        "type": "mermaid",
        "code": b64(code.strip()),
        "pattern": "dotted",
        "color": "white",
        "title": title,
        "claim_id": str(uuid.uuid4()),
        "themeColor": "classic",
        "themeShade": "light",
    }
    return CLAIM + "?" + urllib.parse.urlencode(params)


def markdown_url(code: str, title: str) -> str:
    params = {
        "source": "chatgpt",
        "type": "markdown",
        "code": b64(strip_alerts(code)),
        "title": title,
    }
    return CLAIM + "?" + urllib.parse.urlencode(params)


def check(name: str, url: str) -> None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print(f"{name:22} HTTP {resp.status} | {len(url):5d} chars")
            if resp.status != 200:
                raise SystemExit(f"{name} returned HTTP {resp.status}")
    except urllib.error.HTTPError as err:
        print(f"{name:22} HTTP {err.code} | {len(url):5d} chars")
        if err.code == 414:
            raise SystemExit(
                f"{name} URL too long (HTTP 414). Lower --max-url-chars and rebuild; inspect oversized blocks if splitting cannot fit."
            ) from err
        raise


DEFAULT_HUB = {
    "title": "Statistics Study Kit",
    "editable_stem": "Statistics-Editable-GoodNotes",
    "preview_stem": "Statistics-Preview-GoodNotes",
    "prefix": "Statistics",
    "goodnotes_root": "Monroe University",
    "goodnotes_term": "Current Term",
    "goodnotes_course": "Statistics",
}


def load_hub_meta(kit: Path) -> dict[str, str]:
    """Per-kit import panel. Missing hub.json keeps the Statistics filenames.

    A missing goodnotes_course falls back to this kit's own prefix, never to
    another course's folder; the live contract requires every filing key.
    """
    meta = dict(DEFAULT_HUB)
    path = kit / "hub.json"
    if path.exists():
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("hub.json must be an object")
        for key in DEFAULT_HUB:
            fallback = meta["prefix"] if key == "goodnotes_course" else meta[key]
            value = data.get(key, fallback)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"hub.json {key} must be a nonempty string")
            meta[key] = value.strip()
    for key in ("editable_stem", "preview_stem"):
        stem = meta[key]
        if Path(stem).name != stem or stem.endswith((".html", ".txt")):
            raise ValueError(f"hub.json {key} must be a bare filename stem")
    return meta


def load_preserved(kit: Path) -> dict[str, str]:
    path = kit / "preserved-claims.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


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


def section_week(folder: Path) -> int | None:
    """Positive term week from state.json. Do not infer from Chapter-NN (IT 6.4 is Week 2)."""
    path = folder / "state.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    week = data.get("week") if isinstance(data, dict) else None
    if isinstance(week, bool) or not isinstance(week, int) or week < 1:
        return None
    return week


def section_title(folder: Path, section: str) -> str:
    """Human folder name from state.json; the section number remains the safe fallback."""
    path = folder / "state.json"
    if not path.exists():
        return section
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return section
    title = data.get("title") if isinstance(data, dict) else None
    return title.strip() if isinstance(title, str) and title.strip() else section


def filing_path(*parts: str) -> str:
    return " → ".join(part.strip() for part in parts if part.strip())


def section_folder_name(section: str, title: str) -> str:
    """`3.2 Measures of Variation`; never `1.1 1.1` when the title is missing."""
    title = title.strip()
    if not title or title == section:
        return section
    if title.startswith(section + " "):
        return title
    return f"{section} {title}"


def import_signature(url: str) -> tuple[str, ...]:
    """Import identity without the random Mermaid claim_id."""
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    return tuple(query.get(key, [""])[0] for key in ("type", "code", "title"))


def parse_link_txt(text: str) -> dict[str, str]:
    urls: dict[str, str] = {}
    lines = text.splitlines()
    for name, url in zip(lines, lines[1:]):
        if name.endswith(":") and url.startswith(CLAIM):
            urls[name[:-1]] = url
    return urls


def import_changes(previous: dict[str, str], current: dict[str, str]) -> dict[str, list[str]]:
    """Which buttons need a fresh GoodNotes import after this rebuild."""
    return {
        "new": [name for name in current if name not in previous],
        "changed": [name for name in current if name in previous
                    and import_signature(previous[name]) != import_signature(current[name])],
        "removed": [name for name in previous if name not in current],
    }


NODE_ID = r"[A-Za-z][A-Za-z0-9_]*"
NODE_LINE = re.compile(rf"^\s*({NODE_ID})\s*[\(\[\{{>]")
EDGE_LINE = re.compile(
    rf"^\s*({NODE_ID})\b.*?(?:-->|-\.->|==>|---)\s*(?:\|[^|]*\|\s*)?({NODE_ID})\b")
CLASS_LINE = re.compile(r"^\s*class\s+([A-Za-z0-9_,\s]+?)\s+(\S+)\s*;?\s*$")
LINKSTYLE_LINE = re.compile(r"^\s*linkStyle\s+([\d,\s]+?)\s+(\S.*)$")
CHAPTER_HUB = re.compile(r"^CH(\d+)_\d+$")


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


def map_label(section: str, path: Path) -> str:
    stem = path.stem
    lower = stem.lower()
    if lower.endswith("concept-map"):
        return f"{section} Concept Map"
    if lower.endswith("decision-flow"):
        return f"{section} Quiz Sort"
    rest = stem
    for prefix in (f"stats-{section}-", f"{section}-"):
        if rest.lower().startswith(prefix.lower()):
            rest = rest[len(prefix) :]
            break
    rest = re.sub(r"-?flow$", "", rest, flags=re.I)
    pretty = rest.replace("-", " ").strip().title() or path.stem
    return f"{section} {pretty}"


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


def note_imports(section: str, folder: Path, limit: int) -> list[tuple[str, str]]:
    """Canonical notes win; GoodNotes gets Core only. Practice.md is ignored."""
    canonical = sorted(p for p in folder.glob("*.md")
                       if p.name.lower().endswith("study-notes.md"))
    if len(canonical) > 1:
        raise ValueError(f"{folder}: expected one canonical Study-Notes.md")
    if canonical:
        legacy = [p for suffix, _ in NOTE_SPLIT_SUFFIXES
                  for p in sorted(folder.glob("*.md")) if p.name.endswith(suffix)]
        if legacy:
            # First migration must prove that no legacy edits disappear. Later
            # builds trust only the reviewed hashes of the old split files.
            migration = folder / "notes-migration.json"
            hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in legacy}
            if migration.exists():
                reviewed = json.loads(migration.read_text())
                if reviewed.get("canonical") != canonical[0].name or reviewed.get("legacy_sha256") != hashes:
                    raise ValueError(f"{folder}: legacy notes changed since migration; reconcile before building")
            else:
                nonblank = lambda text: [line for line in text.splitlines() if line.strip()]
                combined = "\n".join(p.read_text() for p in legacy)
                if nonblank(combined) != nonblank(canonical[0].read_text()):
                    raise ValueError(f"{folder}: legacy notes differ from canonical; reconcile before building")
        label = f"{section} Notes"
        return split_notes(extract_core(canonical[0].read_text()), label, limit)
    items = []
    for suffix, label in NOTE_SPLIT_SUFFIXES:
        if suffix != "Notes-Core.md":
            continue
        paths = sorted(p for p in folder.glob("*.md") if p.name.endswith(suffix))
        if len(paths) > 1:
            raise ValueError(f"{folder}: duplicate {suffix}")
        for path in paths:
            items.extend(split_notes(extract_core(path.read_text()), f"{section} Notes", limit))
    return items


def split_notes(text: str, label: str, limit: int) -> list[tuple[str, str]]:
    if not text.strip():
        raise ValueError(f"{label}: empty notes")
    if len(markdown_url(text, label)) <= limit:
        return [(label, text)]
    # Split only at headings outside fences, so paragraphs, tables and worked
    # stems remain intact. An oversized block needs an author-chosen boundary.
    blocks, current = [], []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        if fence is None and re.match(r"^#{1,2} +", line) and current:
            blocks.append("".join(current))
            current = []
        current.append(line)
    if current:
        blocks.append("".join(current))
    if fence is not None:
        raise ValueError(f"{label}: unclosed code fence")
    chunks, current = [], ""
    # Reserve enough label space for the worst possible number of parts.
    budget_label = f"{label} {len(blocks)}/{len(blocks)}"
    for block in blocks:
        if len(markdown_url(block, budget_label)) > limit:
            raise ValueError(f"{label}: a heading block exceeds {limit} URL characters; "
                             "add a meaningful level-2 heading without breaking a stem or table")
        if current and len(markdown_url(current + block, budget_label)) > limit:
            chunks.append(current)
            current = ""
        current += block
    if current:
        chunks.append(current)
    return [(f"{label} {i}/{len(chunks)}", chunk)
            for i, chunk in enumerate(chunks, 1)]


def check_batch(folder: Path, offline: bool) -> None:
    path = folder / "state.json"
    if not path.exists():
        print(f"{folder.name}: legacy section; batch completeness unverified")
        return
    state = json.loads(path.read_text())
    status = state.get("status")
    if status not in {"collecting", "partial", "ready", "complete"}:
        raise ValueError(f"{path}: invalid status")
    if not offline and status not in {"ready", "complete"}:
        raise ValueError(f"{folder.name}: {status}; build an offline preview or wait for release")


def maps_in(section: str, folder: Path) -> list[tuple[str, Path]]:
    files = [
        p
        for p in folder.glob("*.mmd")
        if "overall" not in p.stem.lower()
    ]
    files.sort(key=map_kind_rank)
    return [(map_label(section, p), p) for p in files]


def _button_block(
    heading: str,
    items: list[tuple[str, str, str]],
    backup: list[str],
    destination: str = "",
) -> str:
    e = html.escape
    buttons = []
    for label, css, url in items:
        cls = f" {css}" if css else ""
        buttons.append(
            f'    <a class="btn{cls}" href="{e(url, quote=True)}">{e(label)}</a>'
        )
        backup.append(f"    <p>{e(label)}:<br><code>{e(url)}</code></p>")
    extra = ""
    heading_l = heading.lower()
    if "retrieval" in heading_l:
        extra = (
            "  <p>File these in GoodNotes <b>Retrieval/</b>. Sort maps only. Self-test is Practice.md in Obsidian.</p>\n"
        )
    elif "notes" in heading_l:
        extra = (
            "  <p>File in GoodNotes <b>Notes/</b>. Core only. Tap-to-reveal practice is Practice.md in the vault, not a GoodNotes notebook.</p>\n"
        )
    route = (
        f'  <p class="destination"><b>Place in:</b> <code>{e(destination)}</code></p>\n'
        if destination else ""
    )
    return (
        f"  <h2>{e(heading)}</h2>\n{route}{extra}"
        f'  <div class="row">\n' + "\n".join(buttons) + "\n  </div>"
    )


def week_label(week: int | None) -> str:
    return f"Week {week}" if week else "Unscheduled"


def render_hub(
    title: str,
    course_items: list[tuple[str, str, str]],
    weeks: list[tuple[int | None, list[tuple[str, list[tuple[str, str, str]]]]]],
    extras: list[tuple[str, str]] | None = None,
    destinations: dict[str, str] | None = None,
) -> str:
    e = html.escape
    backup: list[str] = []
    numbered = [week for week, _ in weeks if week]
    latest = max(numbered) if numbered else None
    nav = ""
    if len(weeks) > 1 or (weeks and weeks[0][0]):
        links = []
        for week, _ in weeks:
            slug = f"week-{week}" if week else "unscheduled"
            links.append(f'    <a href="#{slug}">{e(week_label(week))}</a>')
        nav = '  <nav class="week-nav" aria-label="Weeks">\n' + "\n".join(links) + "\n  </nav>"
    destinations = destinations or {}
    course_block = (
        _button_block("Course-wide", course_items, backup, destinations.get("Course-wide", ""))
        if course_items else ""
    )
    week_blocks = []
    for week, sections in weeks:
        slug = f"week-{week}" if week else "unscheduled"
        inner = "\n\n".join(
            _button_block(heading, items, backup, destinations.get(heading, ""))
            for heading, items in sections
        )
        opened = " open" if week == latest or (latest is None and week is None) else ""
        week_blocks.append(
            f'  <details class="week"{opened} id="{slug}">\n'
            f"    <summary>{e(week_label(week))}</summary>\n"
            f"{inner}\n"
            f"  </details>"
        )
    for label, url in extras or []:
        backup.append(f"    <p>{e(label)}:<br><code>{e(url)}</code></p>")
    parts = [p for p in (nav, course_block, *week_blocks) if p]
    body_sections = "\n\n".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{e(title)} - Open in Goodnotes</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ --ink:#1f3a5f; --accent:#2e6e8e; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; min-height:100vh; display:grid; justify-items:center; align-items:start; padding:32px 16px; background:#f5f8fb; font-family:-apple-system, "Helvetica Neue", Arial, sans-serif; color:#24313f; }}
  .card {{ background:#fff; border:1px solid #dde7f0; border-radius:18px; padding:42px 46px; max-width:820px; box-shadow:0 12px 30px rgba(31,58,95,.08); text-align:center; }}
  h1 {{ font-size:22px; margin:0 0 8px; color:var(--ink); }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.8px; color:#7c8fa1; margin:18px 0 0; }}
  p {{ font-size:15px; line-height:1.5; color:#41566b; margin:10px 0; }}
  .destination {{ margin:8px auto 2px; padding:9px 12px; max-width:720px; border:1px solid #d7e4ee; border-radius:10px; background:#eef5f9; text-align:left; }}
  .destination code {{ color:#24313f; font-size:12px; word-break:normal; }}
  .week-nav {{ display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin:16px 0 8px; }}
  .week-nav a {{ font-size:13px; font-weight:600; color:var(--accent); text-decoration:none; padding:6px 14px; border:1px solid #dde7f0; border-radius:999px; }}
  .week-nav a:hover {{ background:#eef3f8; }}
  .week {{ margin:16px 0 8px; text-align:left; border:1px solid #dde7f0; border-radius:14px; padding:4px 16px 14px; background:#fafcfe; }}
  .week > summary {{ cursor:pointer; font-size:16px; font-weight:700; color:var(--ink); padding:12px 4px; list-style:none; }}
  .week > summary::-webkit-details-marker {{ display:none; }}
  .week > summary::after {{ content:" ▾"; color:#7c8fa1; font-weight:400; }}
  .week:not([open]) > summary::after {{ content:" ▸"; }}
  .row {{ display:flex; gap:14px; justify-content:center; flex-wrap:wrap; margin:14px 0 4px; }}
  .btn {{ display:inline-block; padding:13px 24px; background:var(--ink); color:#fff; text-decoration:none; border-radius:999px; font-size:15px; font-weight:600; }}
  .btn.alt {{ background:#2e6e8e; }}
  .btn.green {{ background:#3f7d5c; }}
  .btn.amber {{ background:#b4793a; }}
  .btn.plum {{ background:#5c4a7a; }}
  .btn:hover {{ opacity:.9; }}
  ol {{ text-align:left; font-size:14px; color:#41566b; line-height:1.6; margin:18px 0 0; padding-left:22px; }}
  details.links {{ margin-top:20px; font-size:12px; color:#7c8fa1; text-align:left; }}
  code {{ word-break:break-all; font-size:11px; }}
</style>
</head>
<body>
<div class="card">
  <h1>{e(title)}</h1>
  <p>Editable imports for Goodnotes. Maps and Core notes only. Self-test is <code>Practice.md</code> in Obsidian Reading view. Open one week at a time.</p>
  <p>Create only the folders shown under <b>Place in</b>. If a route is not listed, do not create another folder for it.</p>

{body_sections}

  <ol>
    <li><b>On this Mac:</b> click a button and sign in if asked.</li>
    <li><b>On iPad:</b> AirDrop this file to your iPad, open it in Safari, then tap a button.</li>
    <li>Tap nodes to edit text, drag to rearrange, or write with the pen.</li>
    <li>After each import, move it to the exact <b>Place in</b> route printed above its button.</li>
    <li>Do not import Quiz why or Retrieval prose. After maps + Core, open <code>Practice.md</code> in Obsidian Reading view and tap to check.</li>
    <li>The overall map only includes chapters already studied. Later chapters attach when you send them.</li>
  </ol>
  <details class="links"><summary>Direct links (backup)</summary>
{chr(10).join(backup)}
  </details>
</div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--downloads", action="store_true")
    parser.add_argument("--offline", action="store_true",
                        help="Write a separate preview without contacting GoodNotes")
    parser.add_argument("--max-url-chars", type=int, default=MAX_URL_CHARS)
    args = parser.parse_args()
    kit = args.kit.expanduser().resolve()
    if args.max_url_chars < 500:
        parser.error("--max-url-chars must be at least 500")
    if args.offline and args.downloads:
        parser.error("offline previews cannot be exported to Downloads")
    for _, folder in iter_sections(kit):
        check_batch(folder, args.offline)
    if not args.offline:
        contract = validate_kit.check_kit(kit)
        if contract:
            raise ValueError("Kit contract failed:\n" + "\n".join(contract))
        for warning in validate_kit.kit_warnings(kit):
            print("warning: " + warning)
    derived: list[tuple[Path, str]] = []
    preserved = load_preserved(kit)
    hub_meta = load_hub_meta(kit)
    prefix = hub_meta["prefix"]
    filing_root = filing_path(
        hub_meta["goodnotes_root"],
        hub_meta["goodnotes_term"],
        hub_meta["goodnotes_course"],
    )
    destinations = {
        "Course-wide": filing_path(filing_root, "00 Course Overview"),
    }

    overall = (kit / "overall-flow.mmd").read_text()
    urls: dict[str, str] = {}
    course_row: list[tuple[str, str, str]] = []
    whole = mermaid_url(overall, f"{prefix} Overall Map")
    if len(whole) <= args.max_url_chars:
        urls["Overall Map"] = whole
        course_row.append(("Overall Map", "", whole))
    else:
        print("Overall Map exceeds the URL budget; splitting it by chapter")
        for i, (chapter, part) in enumerate(split_overall(overall)):
            label = f"Overall Map Ch {chapter}"
            urls[label] = mermaid_url(part, f"{prefix} {label}")
            course_row.append((label, BTN[i % len(BTN)] if i else "", urls[label]))
    if "Topic Card" in preserved:
        urls["Topic Card"] = preserved["Topic Card"]
    if "Syllabus preview" in preserved:
        urls["Syllabus preview"] = preserved["Syllabus preview"]

    if "Topic Card" in urls:
        course_row.append(("Topic Card", "alt", urls["Topic Card"]))

    week_map: dict[int | None, list[tuple[str, list[tuple[str, str, str]]]]] = {}
    for section, folder in iter_sections(kit):
        week = section_week(folder)
        week_folder = f"Week {week:02d}" if week else "Unscheduled"
        named_section = section_folder_name(section, section_title(folder, section))
        section_root = filing_path(filing_root, week_folder, named_section)
        legend_items: list[tuple[str, str, str]] = []
        retrieval_items: list[tuple[str, str, str]] = []
        for label, path in maps_in(section, folder):
            urls[label] = mermaid_url(path.read_text(), f"{prefix} {label}")
            css = BTN[len(retrieval_items if retrieval_map(path) else legend_items) % len(BTN)]
            target = retrieval_items if retrieval_map(path) else legend_items
            target.append((label, css, urls[label]))
        note_items: list[tuple[str, str, str]] = []
        for i, (label, code) in enumerate(note_imports(section, folder, args.max_url_chars)):
            urls[label] = markdown_url(code, label)
            derived.append((folder / "imports" / f"notes-{i + 1:02d}.md", code))
            note_items.append((label, BTN[i % len(BTN)], urls[label]))
        bucket = week_map.setdefault(week, [])
        if legend_items:
            heading = f"Chapter {section} maps"
            bucket.append((heading, legend_items))
            destinations[heading] = filing_path(section_root, "Map")
        if retrieval_items:
            heading = f"Chapter {section} Retrieval maps"
            bucket.append((heading, retrieval_items))
            destinations[heading] = filing_path(section_root, "Retrieval")
        if note_items:
            heading = f"Chapter {section} notes"
            bucket.append((heading, note_items))
            destinations[heading] = filing_path(section_root, "Notes")
    week_groups = [(week, week_map[week]) for week in sorted(w for w in week_map if w is not None)]
    if None in week_map:
        week_groups.append((None, week_map[None]))

    for name, url in urls.items():
        if name not in {"Topic Card", "Syllabus preview"} and len(url) > args.max_url_chars:
            raise ValueError(f"{name}: URL exceeds {args.max_url_chars}; simplify the map labels")
        if not args.offline:
            check(name, url)
    if args.offline:
        print("OFFLINE PREVIEW: HTTP and GoodNotes import not verified")

    extras = []
    if "Syllabus preview" in urls:
        extras.append(("Syllabus preview", urls["Syllabus preview"]))
    title = hub_meta["title"] + (" — Unverified preview" if args.offline else "")
    page = render_hub(title, course_row, week_groups, extras, destinations)
    link_txt = "".join(f"{name}:\n{url}\n\n" for name, url in urls.items())

    # All content and URL checks finish before replacing any published output.
    base = hub_meta["preview_stem"] if args.offline else hub_meta["editable_stem"]
    previous_links = kit / f"{base}-link.txt"
    previous = parse_link_txt(previous_links.read_text()) if previous_links.exists() else {}
    changes = import_changes(previous, urls)
    if not args.offline:
        for _, folder in iter_sections(kit):
            canonical = [p for p in folder.glob("*.md") if p.name.lower().endswith("study-notes.md")]
            legacy = [p for suffix, _ in NOTE_SPLIT_SUFFIXES
                      for p in sorted(folder.glob("*.md")) if p.name.endswith(suffix)]
            if canonical and legacy:
                receipt = {"canonical": canonical[0].name,
                           "legacy_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in legacy}}
                path = folder / "notes-migration.json"
                path.with_suffix(".tmp").write_text(json.dumps(receipt, indent=2) + "\n")
                path.with_suffix(".tmp").replace(path)
    for path, code in derived:
        if args.offline:
            continue
        path.parent.mkdir(exist_ok=True)
        path.with_suffix(".tmp").write_text(code)
        path.with_suffix(".tmp").replace(path)
    for path, content in [(kit / f"{base}.html", page),
                          (kit / f"{base}-link.txt", link_txt)]:
        path.with_suffix(path.suffix + ".tmp").write_text(content)
        path.with_suffix(path.suffix + ".tmp").replace(path)
    if args.downloads:
        dl = Path.home() / "Downloads"
        stem = hub_meta["editable_stem"]
        (dl / f"{stem}.html").write_text(page)
        (dl / f"{stem}-link.txt").write_text(link_txt)
    print(f"wrote {base}.html + link txt")
    if not previous:
        print("No previous link txt; every button is a first import")
    elif any(changes.values()):
        for kind in ("new", "changed", "removed"):
            if changes[kind]:
                print(f"{kind.capitalize()} imports: " + "; ".join(changes[kind]))
        print("Re-import only new/changed buttons; delete removed ones in GoodNotes by hand.")
    else:
        print("No import content changed; nothing to re-import in GoodNotes")


if __name__ == "__main__":
    main()
