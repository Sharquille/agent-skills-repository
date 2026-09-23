#!/usr/bin/env python3
"""Read-only checks for source links, overall-map preservation, and kit filing."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

HUB_KEYS = ("title", "editable_stem", "preview_stem", "prefix",
            "goodnotes_root", "goodnotes_term", "goodnotes_course")
PREFIX_BY_COURSE = {
    "MA-235": "Statistics",
    "EN-221": "English",
    "IT-100": "IT",
    "LA-122": "Communication",
}
SKIP_NAMES = {".DS_Store", "README.md"}
STATUSES = {"collecting", "partial", "ready", "complete"}
COVERAGES = {"partial", "full"}
SOURCE_ROW = re.compile(r"^\|\s*S\d+\s*\|", re.M)
OUTCOME_ROW = re.compile(r"^\| (?:\d+[a-z]?) \|")


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
    """Filing contract every model must pass before a live hub.

    Catches the Stats-vs-IT misses: missing hub.json, study-order README,
    COURSE/week pointers, leftover pending/candidate files, and thin sections.
    """
    kit = kit.resolve()
    course = kit.parent
    errors: list[str] = []

    hub_path = kit / "hub.json"
    if not hub_path.is_file():
        errors.append("Missing hub.json; every course needs its own import panel")
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
            for key in ("editable_stem", "preview_stem"):
                stem = str(data.get(key, "")).strip()
                if Path(stem).name != stem or stem.endswith((".html", ".txt")):
                    errors.append(f"hub.json {key} must be a bare filename stem")
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

    for html in list(course.glob("Week*/Work/*Editable-GoodNotes.html")):
        errors.append(f"Do not copy hub HTML into Work/: {html.relative_to(course).as_posix()}")

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
        ledger = folder / "ledger.md"
        if ledger.is_file() and not SOURCE_ROW.search(ledger.read_text()):
            warnings.append(
                f"{folder.relative_to(kit).as_posix()}: ledger.md has no source table rows "
                "(| S001 | ...); claims are legacy/unverified until sources are recorded")
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
