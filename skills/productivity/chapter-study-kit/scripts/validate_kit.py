#!/usr/bin/env python3
"""Read-only checks for source links, overall-map preservation, and kit filing."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

HUB_KEYS = ("title", "prefix", "goodnotes_root", "goodnotes_term", "goodnotes_course")
PREFIX_BY_COURSE = {
    "MA-235": "Statistics",
    "EN-221": "English",
    "IT-100": "IT",
    "LA-122": "Communication",
}
SKIP_NAMES = {".DS_Store", "README.md"}
STATUSES = {"collecting", "ready", "complete"}
COVERAGES = {"partial", "full"}
# "import" is the on-iPad check: the user confirms the notebook reads well in GoodNotes.
VERIFICATIONS = ("local", "render", "import")
CHECK_RESULTS = {"pending", "passed", "failed"}
SOURCE_ROW = re.compile(r"^\|\s*S\d+\s*\|", re.M)
OUTCOME_ROW = re.compile(r"^\| (?:\d+[a-z]?) \|")
# A Practice item that names where something was taught (deck, slide, figure, page)
# tests memory of the source, not understanding. Review pointers are exempt.
SOURCE_LOCATOR = re.compile(
    r"\b(?:PP\d+|slides?\s+\d+|(?:the|this|these|that)\s+(?:slides?|deck|lecture|textbook|handout|figure)"
    r"|on\s+this\s+deck|fig(?:ure|\.)?\s*\d+(?:-\d+)?|page\s+\d+|printed\s+(?:example|answer|key|list)"
    r"|according\s+to\s+the)\b", re.I)


# Figures: an SVG beside the notes, embedded with a Markdown image line.
FIGURE_LINE = re.compile(r"(?m)^!\[([^\]]*)\]\(<?([^)>]+\.svg)>?\)[ \t]*$")
# The map palette (references/visual-language.md) plus the notebook's neutral inks.
FIGURE_COLORS = {
    "#1F3A5F", "#EEF3F8", "#8FA8BE", "#24313F", "#EFE9FA", "#9B8AB8", "#3E3357",
    "#F8F4FD", "#B9A9D1", "#4A3D63", "#E7F4EC", "#6FA98A", "#2F4F3C", "#F3FAF6",
    "#93C2A8", "#37543F", "#FBEFE3", "#C98F5A", "#5C4023", "#FEF8F1", "#DBAC7E",
    "#654626", "#FFFFFF", "#1F2933", "#5B6B7A", "#C9D3DD",
}
FIGURE_FORBIDDEN = re.compile(
    r"<script|<foreignObject|<image\b|<iframe|\bon[a-z]+\s*=|javascript:|@import"
    r"|(?:xlink:)?href\s*=\s*\"(?!#)|url\(\s*(?!#)", re.I)
# A multi-digit, decimal, or percent value in a figure must come from the notes or ledger.
FIGURE_NUMBER = re.compile(r"\d+(?:[.,]\d+)?%?")


def check_figures(folder: Path, notes: Path) -> list[str]:
    """Figures are safe, accessible, on-palette SVGs whose numbers the sources supply."""
    errors = []
    notes_text = notes.read_text()
    ledger = folder / "ledger.md"
    evidence = notes_text + (ledger.read_text() if ledger.is_file() else "")
    referenced = {}
    for alt, name in FIGURE_LINE.findall(notes_text):
        if "/" in name or "\\" in name:
            errors.append(f"figure {name} must sit beside the notes, not in another folder")
            continue
        if not alt.strip():
            errors.append(f"figure {name} needs alt text in its Markdown image line")
        referenced[name] = alt
    for name in referenced:
        if not (folder / name).is_file():
            errors.append(f"figure {name} is referenced but missing")
    for svg_path in sorted(folder.glob("*.svg")):
        name = svg_path.name
        if name not in referenced:
            errors.append(f"figure {name} is not referenced from the notes")
        svg = svg_path.read_text()
        if FIGURE_FORBIDDEN.search(svg):
            errors.append(f"figure {name} has a script, external link, or embedded image")
        if not re.search(r'<svg[^>]*\brole="img"', svg) or not re.search(r'<svg[^>]*\baria-label="[^"]+"', svg):
            errors.append(f"figure {name} needs role=\"img\" and an aria-label on <svg>")
        odd = sorted({c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", svg)} - FIGURE_COLORS)
        if odd:
            errors.append(f"figure {name} uses colours outside the palette: {', '.join(odd)}")
        labels = " ".join(html.unescape(x) for x in re.findall(r"<text[^>]*>([^<]*)</text>", svg))
        for number in sorted(set(FIGURE_NUMBER.findall(labels))):
            digits = re.sub(r"\D", "", number)
            if (len(digits) >= 2 or "%" in number or "." in number) and number not in evidence:
                errors.append(f"figure {name} shows {number}, which the notes and ledger do not")
    return errors


# Worked examples: every number is given or produced by a visible step (notes-contract.md).
WORKED_START = re.compile(r"(?m)^\*\*Worked example:\s*(.+?)\*\*\s*$")
WORKED_PARTS = ("Situation", "Given", "Steps", "Answer", "Check")
WORKED_LABELS = re.compile(
    r"\b(?:Examples?|Figures?|Fig\.?|Tables?|Core|Chapters?|Sections?|Q|formulas?)\s*\(?\d+(?:[-.]\d+)*[a-z]?\)?"
    r"|\(\d+\)|^\s*\d+\.\s", re.I | re.M)
WORKED_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")
WORKED_CONSTANTS = {0.0, 1.0, 100.0}


def worked_numbers(text: str) -> list[str]:
    return WORKED_NUMBER.findall(WORKED_LABELS.sub(" ", text))


def check_worked_examples(notes_text: str) -> list[str]:
    """Each worked example has its five parts and no number from nowhere."""
    errors = []
    starts = list(WORKED_START.finditer(notes_text))
    for i, start in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(notes_text)
        # The example ends at the next heading, its TEST MOVE, or a figure line.
        heading = re.search(r"(?m)^(?:#|\*\*TEST MOVE:\*\*|!\[)", notes_text[start.end():end])
        block = notes_text[start.end():start.end() + heading.start()] if heading else notes_text[start.end():end]
        title = start.group(1).strip()
        marks = {part: re.search(rf"(?m)^\*\*{part}:\*\*", block) for part in WORKED_PARTS}
        missing = [part for part, m in marks.items() if not m]
        if missing:
            errors.append(f"Worked example: {title}: needs {', '.join(missing)}")
            continue
        pos = [marks[part].start() for part in WORKED_PARTS]
        if pos != sorted(pos):
            errors.append(f"Worked example: {title}: parts must run Situation, Given, Steps, Answer, Check")
            continue
        piece = {part: block[pos[k]:pos[k + 1] if k + 1 < len(pos) else len(block)]
                 for k, part in enumerate(WORKED_PARTS)}
        known = set(WORKED_CONSTANTS) | {float(n) for n in worked_numbers(piece["Situation"] + piece["Given"])}
        unexplained = []
        steps = re.split(r"(?m)^\s*\d+\.\s", piece["Steps"].split("**", 2)[-1])
        for step in steps:
            parts = re.split(r"=|≈|\\approx", step)  # what follows is produced by the step
            unexplained += [n for n in worked_numbers(parts[0]) if float(n) not in known]
            for later in parts[1:]:
                known |= {float(n) for n in worked_numbers(later)}
        unexplained += [n for n in worked_numbers(piece["Answer"]) if float(n) not in known]
        # A check may recompute: its inputs are traced like a step's, its results are new.
        check = re.split(r"=|≈|\\approx", piece["Check"])
        unexplained += [n for n in worked_numbers(check[0]) if float(n) not in known]
        for i, later in enumerate(check[1:], 1):
            head = re.split(r"[,.;]\s|\$\s", later, maxsplit=1)
            known |= {float(n) for n in worked_numbers(head[0])}
            if len(head) > 1:
                unexplained += [n for n in worked_numbers(head[1]) if float(n) not in known]
        for number in dict.fromkeys(unexplained):
            errors.append(f"Worked example: {title}: {number} appears with no source; "
                          "add it to Given or show the step that produces it")
    return errors


def missing_links(path: Path) -> list[str]:
    missing = []
    for target in re.findall(r'\]\((<[^>]+>|[^)]+)\)', path.read_text()):
        target = target.strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme or not parsed.path:
            continue
        if not (path.parent / unquote(parsed.path)).exists():
            missing.append(target)
    return missing


def map_statements(path: Path) -> set[str]:
    """Conservative preservation check, not a general Mermaid parser.

    The skill uses one node or edge per line; edits to labels also need review.
    Whitespace inside a label remains significant.
    """
    statements = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(('%%', 'flowchart ', 'classDef ', 'class ', 'linkStyle ')):
            continue
        statements.add(line.rstrip(';'))
    return statements


def check_map(previous: Path, candidate: Path) -> list[str]:
    return sorted(map_statements(previous) - map_statements(candidate))


def map_direction(path: Path) -> str | None:
    for line in path.read_text().splitlines():
        match = re.match(r"\s*(?:flowchart|graph)\s+(LR|RL|TD|TB|BT)\b", line)
        if match:
            return match.group(1)
    return None


def section_folders(kit: Path) -> list[Path]:
    found = []
    for chapter in sorted(kit.glob("Chapter-*")):
        if not chapter.is_dir():
            continue
        for folder in sorted(chapter.iterdir()):
            if folder.is_dir() and re.match(r"^\d+(\.\d+)*$", folder.name):
                found.append(folder)
    return found


def week_folders(course: Path) -> list[Path]:
    return sorted(p for p in course.iterdir()
                  if p.is_dir() and re.match(r"^Weeks?-?\d", p.name))


def real_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return [p for p in folder.iterdir() if p.is_file() and p.name not in SKIP_NAMES]


def check_practice(practice: Path, plan: Path) -> list[str]:
    """Reconcile eligible folded questions with the source-outcome plan."""
    errors = []
    text = practice.read_text()
    blocks = re.split(r'(?=^> \[!question\]- Q\d+\.)', text, flags=re.M)
    cards = [block for block in blocks if block.startswith('> [!question]- Q')]
    ids = [int(re.match(r'> \[!question\]- Q(\d+)\.', block).group(1)) for block in cards]
    if ids != list(range(1, len(ids) + 1)):
        errors.append('question IDs must be consecutive from Q01')
    for number, block in zip(ids, cards):
        for marker in ('**Answer:**', '**Why:**', '**Review:**'):
            if marker not in block:
                errors.append(f'Q{number:02d} needs {marker}')
        locator = SOURCE_LOCATOR.search(block.split('**Review:**')[0])
        if locator:
            errors.append(f'Q{number:02d} cites the source ("{locator.group(0)}"); '
                          'ask about the idea in a situation instead')

    planned = plan.read_text()
    match = re.search(r'Q_min\s*=\s*A\s*\+\s*H\s*=\s*(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)', planned)
    if not match:
        return errors + ['practice-plan.md needs Q_min = A + H = integers']
    outcomes, flagged, minimum = map(int, match.groups())
    if minimum != outcomes + flagged:
        errors.append('practice-plan.md arithmetic does not reconcile')
    rows = []
    for line in planned.splitlines():
        if not OUTCOME_ROW.match(line):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) != 6:
            errors.append(f'practice-plan.md malformed outcome row: {line}')
            continue
        rows.append(cells)
    if len(rows) != outcomes:
        errors.append(f'practice-plan.md lists {len(rows)} outcomes, expected {outcomes}'
                      + ('; outcome rows must start with a numeric ID such as "| 1 |" or "| 2a |"'
                         if not rows else ''))
    risk_rows = sum(reason not in {'—', '-', ''} for _, _, _, reason, _, _ in rows)
    if risk_rows != flagged:
        errors.append(f'practice-plan.md flags {risk_rows} outcomes, expected {flagged}')
    mapped = []
    for outcome, _, _, reason, primary, extra in rows:
        first = re.findall(r'Q\d+', primary)
        additional = re.findall(r'Q\d+', extra)
        if len(first) != 1:
            errors.append(f'outcome {outcome} needs one primary item')
        if reason not in {'—', '-', ''} and not additional:
            errors.append(f'flagged outcome {outcome} needs a varied extra item')
        mapped.extend(int(item[1:]) for item in first + additional)
    if sorted(mapped) != sorted(ids):
        errors.append('practice-plan.md must map each question ID exactly once')
    if len(ids) < minimum:
        errors.append(f'Practice.md has {len(ids)} questions, below planned minimum {minimum}')
    return errors


def check_state(state_path: Path) -> list[str]:
    try:
        state = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return ["state.json is not valid JSON"]
    if not isinstance(state, dict):
        return ["state.json must be an object"]
    errors = []
    week = state.get("week")
    if isinstance(week, bool) or not isinstance(week, int) or week < 1:
        errors.append("state.json needs a positive integer week")
    if state.get("status") not in STATUSES:
        errors.append(f"state.json status must be one of {', '.join(sorted(STATUSES))}")
    if state.get("coverage") not in COVERAGES:
        errors.append(f"state.json coverage must be one of {', '.join(sorted(COVERAGES))}")
    title = state.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("state.json needs a short human title for the GoodNotes route")
    verification = state.get("verification")
    if state.get("status") == "complete" and not (
            isinstance(verification, dict)
            and all(verification.get(key) == "passed" for key in VERIFICATIONS)):
        errors.append("state.json complete needs verification local, render, and import all passed")
    return errors


def check_section(folder: Path) -> list[str]:
    """Per-section filing contract; usable while other sections still collect."""
    errors: list[str] = []
    if not (folder / "ledger.md").is_file():
        errors.append("missing ledger.md")
    state_path = folder / "state.json"
    if not state_path.is_file():
        errors.append("missing state.json")
    else:
        errors += check_state(state_path)
    practice = folder / "Practice.md"
    plan = folder / "practice-plan.md"
    if not practice.is_file():
        errors.append("missing Practice.md")
    elif "[!question]-" not in practice.read_text():
        errors.append("Practice.md needs folded [!question]- callouts")
    if not plan.is_file():
        errors.append("missing practice-plan.md")
    elif practice.is_file():
        errors += check_practice(practice, plan)
    notes = [p for p in folder.glob("*.md") if p.name.lower().endswith("study-notes.md")]
    if len(notes) != 1:
        errors.append("need exactly one *Study-Notes.md")
    else:
        errors += check_figures(folder, notes[0])
        errors += check_worked_examples(notes[0].read_text())
    concept = sorted(folder.glob("*-concept-map.mmd"))
    sort_maps = sorted(folder.glob("*-decision-flow.mmd"))
    if not concept:
        errors.append("missing *-concept-map.mmd")
    if not sort_maps:
        errors.append("missing *-decision-flow.mmd")
    for path in concept:
        if map_direction(path) != "LR":
            errors.append(f"{path.name} must be flowchart LR (concept map)")
    for path in sort_maps + sorted(folder.glob("*-error-flow.mmd")):
        if map_direction(path) not in {"TD", "TB"}:
            errors.append(f"{path.name} must be flowchart TD (quiz sort)")
    for pending in folder.glob("ocr-*.pending.txt"):
        errors.append(f"leftover pending OCR: {pending.name}")
    return errors


def check_kit(kit: Path) -> list[str]:
    """Filing contract every model must pass before building notebooks.

    Catches the Stats-vs-IT misses: missing hub.json, study-order README,
    COURSE/week pointers, leftover pending/candidate files, and thin sections.
    """
    kit = kit.resolve()
    course = kit.parent
    errors: list[str] = []

    hub_path = kit / "hub.json"
    if not hub_path.is_file():
        errors.append("Missing hub.json; every course needs its own course name and GoodNotes route")
    else:
        try:
            data = json.loads(hub_path.read_text())
        except json.JSONDecodeError as error:
            errors.append(f"hub.json is not JSON: {error}")
            data = {}
        if data and (not isinstance(data, dict) or any(
                not isinstance(data.get(key), str) or not data[key].strip()
                for key in HUB_KEYS)):
            errors.append("hub.json needs nonempty " + ", ".join(HUB_KEYS))
        if isinstance(data, dict):
            prefix = str(data.get("prefix", "")).strip()
            expected = PREFIX_BY_COURSE.get(course.name)
            if expected and prefix != expected:
                errors.append(
                    f"hub.json prefix {prefix!r} does not match {course.name} ({expected})")
            for other_course, other_prefix in PREFIX_BY_COURSE.items():
                if other_course != course.name and prefix == other_prefix:
                    errors.append(
                        f"hub.json prefix {prefix!r} belongs to {other_course}, not {course.name}")

    readme = kit / "README.md"
    if not readme.is_file():
        errors.append("Missing Chapter-Kits/README.md")
    else:
        text = readme.read_text()
        for marker in ("Map", "Practice.md", "Retrieval"):
            if marker not in text:
                errors.append(f"Chapter-Kits/README.md must name {marker} in the study order")

    sources = kit / "SOURCES.md"
    if not sources.is_file():
        errors.append("Missing SOURCES.md")
    else:
        errors += ["Missing source: " + p for p in missing_links(sources)]

    if not (kit / "overall-flow.mmd").is_file():
        errors.append("Missing overall-flow.mmd")
    if not (kit / "overall-flow.prev.mmd").is_file():
        errors.append("Missing overall-flow.prev.mmd")
    if (kit / "overall-flow.candidate.mmd").exists():
        errors.append("Leftover overall-flow.candidate.mmd; delete after promote")

    folders = section_folders(kit)
    section_set = set(folders)
    for pending in kit.rglob("ocr-*.pending.txt"):
        if pending.parent not in section_set:
            errors.append(f"Leftover pending OCR: {pending.relative_to(kit)}")
    if not folders:
        errors.append("No Chapter-NN/<section>/ folders")
    seen_chapters = set()
    for folder in folders:
        rel = folder.relative_to(kit).as_posix()
        errors += [f"{rel}: {problem}" for problem in check_section(folder)]
        chapter = folder.parent
        if chapter not in seen_chapters:
            seen_chapters.add(chapter)
            if not (chapter / "README.md").is_file():
                errors.append(f"{chapter.relative_to(kit).as_posix()}: missing README.md")

    course_md = course / "COURSE.md"
    if course_md.is_file() and "Chapter-Kits" not in course_md.read_text():
        errors.append("COURSE.md must point at Chapter-Kits")

    for week in week_folders(course):
        materials = week / "Materials"
        if not real_files(materials):
            continue
        for sub, label in ((materials, "Materials/README.md"), (week / "Work", "Work/README.md")):
            readme_path = sub / "README.md"
            if not readme_path.is_file() or "Chapter-Kits" not in readme_path.read_text():
                errors.append(f"{week.name}/{label} must exist and point at Chapter-Kits")

    return errors


def kit_warnings(kit: Path) -> list[str]:
    """Advisory gaps that do not block a legacy kit from publishing."""
    kit = kit.resolve()
    warnings = []
    if kit.parent.name not in PREFIX_BY_COURSE:
        warnings.append(
            f"{kit.parent.name} is not in PREFIX_BY_COURSE; the cross-course prefix check "
            "only guards the known courses")
    for folder in section_folders(kit):
        rel = folder.relative_to(kit).as_posix()
        ledger = folder / "ledger.md"
        if ledger.is_file() and not SOURCE_ROW.search(ledger.read_text()):
            warnings.append(
                f"{rel}: ledger.md has no source table rows "
                "(| S001 | ...); claims are legacy/unverified until sources are recorded")
        try:
            state = json.loads((folder / "state.json").read_text())
        except (OSError, json.JSONDecodeError):
            continue  # check_kit already reports a missing or broken state.json
        verification = state.get("verification") if isinstance(state, dict) else None
        odd = [key for key in VERIFICATIONS
               if not isinstance(verification, dict) or verification.get(key) not in CHECK_RESULTS]
        if odd:
            warnings.append(f"{rel}: state.json verification {', '.join(odd)} should be "
                            "pending, passed, or failed")
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", type=Path, help="Chapter-Kits folder; run the full filing contract")
    parser.add_argument("--section", type=Path,
                        help="One Chapter-NN/<section> folder; check it alone")
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    if bool(args.previous) != bool(args.candidate):
        parser.error("--previous and --candidate are required together")
    if not (args.kit or args.section or args.sources or args.previous):
        parser.error("supply --kit, --section, --sources, or a map pair")
    errors = []
    warnings = []
    if args.kit:
        errors += check_kit(args.kit)
        warnings += kit_warnings(args.kit)
    if args.section:
        if not args.section.is_dir():
            parser.error(f"{args.section} is not a folder")
        errors += [f"{args.section.name}: {problem}" for problem in check_section(args.section)]
    if args.sources:
        errors += ["Missing source: " + p for p in missing_links(args.sources)]
    if args.previous:
        errors += ["Removed or changed map statement: " + s
                   for s in check_map(args.previous, args.candidate)]
    for warning in warnings:
        print("warning: " + warning)
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print("Local checks passed; source grounding and visual rendering still require review.")


if __name__ == "__main__":
    main()
