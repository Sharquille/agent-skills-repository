#!/usr/bin/env python3
"""Scope a competency loop over a chapter-study-kit, and log attempts.

  competency.py scope --kit <course>/Chapter-Kits --chapters 1-3 [--sections 2.1,3.2]
  competency.py log --section <section dir> --item "Core 5 · read the result" \
      --result correct|partial|missed --reason "..." --next "2026-09-30, Core 5 · compute"

Concepts are a section's numbered Core headings. study-log.md rows (the kit's
attempt log) map to a concept by "Core N" in the Item cell, or by a Practice
question ID through practice-plan.md. Standard library only.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

LOG_HEADER = "| Date | Item | Result | Reason given | Next review |\n| --- | --- | --- | --- | --- |\n"
RESULTS = {"correct", "partial", "missed"}
HEADING = re.compile(r"^#{2,3} (\d+)\. (.+?)\s*$")
CORE_END = re.compile(r"^# .*(Quiz why|Retrieval)", re.I)


def chapter_range(spec):
    lo, _, hi = spec.partition("-")
    return set(range(int(lo), int(hi or lo) + 1))


def core_concepts(section):
    """Numbered Core headings, in order, from the section's canonical notes."""
    notes = sorted(section.glob("*Study-Notes.md"))
    if not notes:
        return []
    out = []
    for line in notes[0].read_text(encoding="utf-8").splitlines():
        if CORE_END.match(line):
            break
        m = HEADING.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def question_to_core(section):
    """Practice question ID -> Core number, from practice-plan.md anchors."""
    plan = section / "practice-plan.md"
    mapping = {}
    if not plan.is_file():
        return mapping
    for line in plan.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d+[a-z]? \|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        core = re.search(r"Core (\d+)", cells[1]) if len(cells) > 1 else None
        if core:
            for qid in re.findall(r"Q\d+", " ".join(cells[4:])):
                mapping[qid] = int(core.group(1))
    return mapping


def read_log(section):
    log = section / "study-log.md"
    rows = []
    if not log.is_file():
        return rows
    for line in log.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not re.match(r"\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        rows.append(dict(date=cells[0], item=cells[1], result=cells[2].lower(), next=cells[4]))
    return rows


def concept_of(item, qmap):
    m = re.search(r"Core (\d+)", item)
    if m:
        return int(m.group(1))
    q = re.search(r"Q\d+", item)
    return qmap.get(q.group(0)) if q else None


def lens_of(item):
    return item.split("·", 1)[1].strip() if "·" in item else item.strip()


def status(rows):
    """unassessed | fragile | developing | secure.

    Secure mirrors chapter-study-kit's check: three unaided correct attempts in a
    row, on three separate dates, using at least two different lenses or items.
    """
    if not rows:
        return "unassessed"
    if rows[-1]["result"] != "correct":
        return "fragile"
    run = []
    for r in reversed(rows):
        if r["result"] != "correct":
            break
        run.append(r)
    dates = {r["date"] for r in run}
    lenses = {lens_of(r["item"]) for r in run}
    if len(run) >= 3 and len(dates) >= 3 and len(lenses) >= 2:
        return "secure"
    return "developing"


def covers(blurb, sid):
    """True if a README blurb names this section ("section 3.1", "sections 3.1–3.2"),
    or names no section at all (then it can't be ruled out)."""
    spans = re.findall(r"sections? (\d+\.\d+)(?:\s*[–-]\s*(\d+\.\d+))?", blurb)
    if not spans:
        return True
    key = tuple(int(x) for x in sid.split("."))
    for lo, hi in spans:
        a = tuple(int(x) for x in lo.split("."))
        b = tuple(int(x) for x in (hi or lo).split("."))
        if a <= key <= b:
            return True
    return False


def eli5_pages(kit, week, sid):
    """ELI5 pages in the section's week Work folder that cover this section."""
    course = kit.parent
    weeks = [d for d in course.glob(f"Week-{week:02d}_*") if d.is_dir()]
    if len(weeks) != 1:
        return []
    work = weeks[0] / "Work"
    readme = (work / "README.md").read_text(encoding="utf-8") if (work / "README.md").is_file() else ""
    pages = []
    for page in sorted(work.glob("*-eli5.html")):
        blurb = next((ln.split("—", 1)[1].strip() for ln in readme.splitlines()
                      if page.name in ln and "—" in ln), "")
        if covers(blurb, sid):
            pages.append(dict(file=str(page), blurb=blurb))
    return pages


def scope(kit, chapters=None, sections=None):
    kit = Path(kit)
    out = []
    for state_path in sorted(kit.glob("Chapter-*/*/state.json")):
        section = state_path.parent
        sid = section.name
        chapter = int(sid.split(".")[0])
        if sections and sid not in sections:
            continue
        if not sections and chapters and chapter not in chapters:
            continue
        state = json.loads(state_path.read_text(encoding="utf-8"))
        qmap = question_to_core(section)
        log = read_log(section)
        concepts = []
        for num, title in core_concepts(section):
            rows = [r for r in log if concept_of(r["item"], qmap) == num]
            concepts.append(dict(core=num, title=title, status=status(rows),
                                 attempts=len(rows), next=rows[-1]["next"] if rows else ""))
        out.append(dict(section=sid, title=state.get("title", ""), week=state.get("week"),
                        path=str(section), concepts=concepts, eli5=eli5_pages(kit, state.get("week", 0), sid)))
    return out


def render(sections):
    lines = []
    for s in sections:
        lines.append(f"## {s['section']} {s['title']} (week {s['week']})")
        lines.append(f"path: {s['path']}")
        lines.append("| Core | Concept | Status | Attempts | Next review |")
        lines.append("| --- | --- | --- | --- | --- |")
        for c in s["concepts"]:
            lines.append(f"| {c['core']} | {c['title']} | {c['status']} | {c['attempts']} | {c['next'] or '—'} |")
        if s["eli5"]:
            lines.append("ELI5 pages this week:")
            lines.extend(f"- {p['file']} — {p['blurb']}" for p in s["eli5"])
        lines.append("")
    return "\n".join(lines)


def log_attempt(section, item, result, reason, next_review, date=None):
    if result not in RESULTS:
        raise ValueError(f"result must be one of {sorted(RESULTS)}")
    for cell in (item, reason, next_review):
        if "|" in cell or "\n" in cell:
            raise ValueError("cells cannot contain '|' or line breaks")
    section = Path(section)
    if not (section / "state.json").is_file():
        raise ValueError(f"{section} is not a chapter-study-kit section (no state.json)")
    log = section / "study-log.md"
    text = log.read_text(encoding="utf-8") if log.is_file() else f"# {section.name} study log\n\n{LOG_HEADER}"
    if "| Date | Item | Result |" not in text:
        text = text.rstrip("\n") + "\n\n" + LOG_HEADER
    row = f"| {date or dt.date.today().isoformat()} | {item} | {result} | {reason} | {next_review} |\n"
    log.write_text(text.rstrip("\n") + "\n" + row, encoding="utf-8")
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scope a competency loop, or log an attempt.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scope")
    sc.add_argument("--kit", required=True, help="<course>/Chapter-Kits")
    sc.add_argument("--chapters", help="e.g. 1-3")
    sc.add_argument("--sections", help="comma list, e.g. 2.1,3.2")
    sc.add_argument("--json", action="store_true")
    lg = sub.add_parser("log")
    lg.add_argument("--section", required=True)
    lg.add_argument("--item", required=True, help='"Core N · lens" or a Practice ID like "Q07"')
    lg.add_argument("--result", required=True)
    lg.add_argument("--reason", required=True)
    lg.add_argument("--next", required=True, dest="next_review")
    lg.add_argument("--date")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "scope":
            secs = set(args.sections.split(",")) if args.sections else None
            data = scope(args.kit, chapter_range(args.chapters) if args.chapters else None, secs)
            if not data:
                print("no processed sections match that range")
                return 1
            print(json.dumps(data, indent=2) if args.json else render(data))
        else:
            print(log_attempt(args.section, args.item, args.result, args.reason, args.next_review, args.date), end="")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
