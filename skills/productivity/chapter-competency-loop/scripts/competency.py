#!/usr/bin/env python3
"""Scope a competency loop over a chapter-study-kit, log attempts, and keep the session tracker.

  competency.py scope --kit <course>/Chapter-Kits --chapters 1-3 [--sections 2.1,3.2]
  competency.py log --section <section dir> --item "Core 5 · read the result" \
      --result correct|partial|missed --reason "..." --next "2026-09-30, Core 5 · compute" \
      [--answers <queue id>] [--kind harder|same|twin] [--no-queue]
  competency.py week --course <course dir> [--date YYYY-MM-DD]
  competency.py tracker show|set --course <course dir> [key=value ...]
  competency.py queue add|tick|due|done --course <course dir> [...]

The tracker (<course>/competency-tracker.json) records what the loop is for (goal,
goal date, chapters), where this session saves files (week and Work folder), the
round, and the re-check queue. Change it only after the learner confirms. `log`
keeps the queue in step with the log: every scored answer, correct included,
queues its follow-up re-check, and `--answers` closes the one it answered.

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


LENSES = ["plain words", "why it matters", "how it works", "real-world map", "contrast", "error hunt",
          "predict", "teach-back", "which tool", "anatomy", "compute", "read the result", "stress test", "value"]
# Retention checks for a concept already answered right: bug hunts first. Never
# re-ask a lens the learner has already passed for that concept.
RETENTION = ["error hunt", "stress test", "contrast", "teach-back"]
MARK = {"correct": "✓", "partial": "~", "missed": "✗"}


def lenses_in(item):
    item = item.lower()
    return [lens for lens in LENSES if lens in item]


def tried(rows):
    """Each lens used on a concept with its latest result, e.g. 'real-world map ✓'."""
    seen = {}
    for r in rows:
        for lens in lenses_in(r["item"]) or (["breakdown"] if "breakdown" in r["item"].lower() else []):
            seen[lens] = MARK.get(r["result"], "?")
    return ", ".join(f"{lens} {m}" for lens, m in seen.items())


def next_check(rows, today=None):
    """What kind of question this concept needs next, so a shown concept isn't re-asked the same way."""
    st = status(rows)
    if st == "unassessed":
        return "first check: plain words or real-world map"
    if st == "fragile":
        return "twin in a new scenario (queued); same lens is fine"
    passed = {lens for r in rows if r["result"] == "correct" for lens in lenses_in(r["item"])}
    fresh = [lens for lens in RETENTION if lens not in passed]
    lens = fresh[0] if fresh else "teach-back in a new scenario"
    if st == "secure":
        due = rows[-1]["next"].split(",")[0].strip()
        if re.match(r"\d{4}-\d{2}-\d{2}$", due) and (today or dt.date.today().isoformat()) < due:
            return f"secure: don't ask before {due}, then retention {lens}"
        return f"secure: retention {lens} only"
    return f"retention: {lens} (passed: {', '.join(sorted(passed)) or 'none'})"


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
            concepts.append(dict(core=num, title=title, status=status(rows), attempts=len(rows),
                                 next=rows[-1]["next"] if rows else "", tried=tried(rows),
                                 check=next_check(rows)))
        out.append(dict(section=sid, title=state.get("title", ""), week=state.get("week"),
                        path=str(section), concepts=concepts, eli5=eli5_pages(kit, state.get("week", 0), sid)))
    return out


def chapter_summary(sections):
    """One line per chapter: how much of it has been checked, and how well."""
    chapters = {}
    for s in sections:
        chapters.setdefault(s["section"].split(".")[0], []).extend(c["status"] for c in s["concepts"])
    lines = ["# Coverage by chapter"]
    for ch, sts in chapters.items():
        counts = {k: sts.count(k) for k in ("secure", "developing", "fragile", "unassessed")}
        lines.append(f"- Chapter {ch}: {len(sts)} concepts · {len(sts) - counts['unassessed']} checked "
                     f"({counts['secure']} secure, {counts['developing']} developing, {counts['fragile']} fragile) "
                     f"· {counts['unassessed']} not yet checked")
    return lines + [""]


def render(sections):
    lines = chapter_summary(sections)
    for s in sections:
        lines.append(f"## {s['section']} {s['title']} (week {s['week']})")
        lines.append(f"path: {s['path']}")
        lines.append("| Core | Concept | Status | Lenses tried | Next check | Next review |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for c in s["concepts"]:
            lines.append(f"| {c['core']} | {c['title']} | {c['status']} | {c['tried'] or '—'} | "
                         f"{c['check']} | {c['next'] or '—'} |")
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


WEEK_DIR = re.compile(r"^Weeks?-(\d+)(?:-\d+)?_(?:[A-Za-z]+_)?(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})$")
TRACKER = "competency-tracker.json"
TRACKER_KEYS = {"goal", "goal_date", "chapters", "week", "work"}


def week_for(course, date=None):
    """The week folder whose date range contains `date` (default today)."""
    day = date or dt.date.today().isoformat()
    for d in sorted(Path(course).iterdir()):
        m = WEEK_DIR.match(d.name)
        if d.is_dir() and m and m.group(2) <= day <= m.group(3):
            return dict(week=int(m.group(1)), folder=str(d), work=str(d / "Work"), start=m.group(2), end=m.group(3))
    raise ValueError(f"no week folder in {course} covers {day}")


def load_tracker(course):
    path = Path(course) / TRACKER
    if not path.is_file():
        return {"course": Path(course).name, "queue": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_tracker(course, data):
    data["updated"] = dt.date.today().isoformat()
    (Path(course) / TRACKER).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def tracker_set(course, pairs):
    data = load_tracker(course)
    for pair in pairs:
        key, _, value = pair.partition("=")
        if key not in TRACKER_KEYS or not value:
            raise ValueError(f"set takes key=value with key in {sorted(TRACKER_KEYS)}")
        if key == "week":
            value = int(value)
            match = []
            for d in sorted(Path(course).iterdir()):
                m = re.match(r"^Weeks?-(\d+)(?:-(\d+))?_", d.name)
                if d.is_dir() and m and int(m.group(1)) <= value <= int(m.group(2) or m.group(1)):
                    match.append(str(d))
            if len(match) != 1:
                raise ValueError(f"expected one folder for week {value}, found {match}")
            data["work"] = str(Path(match[0]) / "Work")
        data[key] = value
    save_tracker(course, data)
    return data


def queue_cmd(course, action, section=None, core=None, kind="twin", count=1, gap=3, qid=None,
              lens="", due="", origin=""):
    """Re-check queue: twins wait until `gap` other questions have been asked."""
    data = load_tracker(course)
    q = data.setdefault("queue", [])
    if action == "add":
        for _ in range(count):
            nid = max([i["id"] for i in q], default=0) + 1
            q.append(dict(id=nid, section=section, core=int(core), kind=kind, gap=gap, since=0,
                          lens=lens, due=due, origin=origin))
    elif action == "tick":
        for item in q:
            item["since"] += 1
    elif action == "done":
        data["queue"] = [i for i in q if i["id"] != int(qid)]
    save_tracker(course, data)
    return [i for i in data["queue"] if i["since"] >= i["gap"]] if action == "due" else data["queue"]


# What each result earns: correct answers come back too, harder (error hunt, stress
# test, contrast), so a right answer is reinforced instead of checked off.
FOLLOW_UP = {"correct": ("harder", 1), "partial": ("same", 1), "missed": ("twin", 2)}
# Breakdown steps and unscored checks queue nothing: the question they break down
# already queued its twins.
NO_FOLLOW_UP = re.compile(r"breakdown|not scored|\bstep\b", re.I)


def course_of(section):
    """<course> for a <course>/Chapter-Kits/Chapter-XX/<section> path, else None."""
    section = Path(section).resolve()
    return section.parents[2] if section.parents[1].name == "Chapter-Kits" else None


def follow_up(section, item, result, next_review, kind=None, answers=None):
    """Queue the re-check a logged answer earns; close the queued one it answered.

    Returns the new queue entries. Nothing is queued for breakdown steps, for
    items with no Core number, or once the concept is secure.
    """
    course = course_of(section)
    if course is None:
        return []
    if answers:
        queue_cmd(course, "done", qid=answers)
    section = Path(section)
    core = concept_of(item, question_to_core(section))
    if core is None or NO_FOLLOW_UP.search(item):
        return []
    rows = [r for r in read_log(section) if concept_of(r["item"], question_to_core(section)) == core]
    if status(rows) == "secure":
        return []
    default_kind, count = FOLLOW_UP[result]
    kind = kind or default_kind
    count = count if kind == "twin" else 1
    due, _, planned = next_review.partition(",")
    before = {i["id"] for i in load_tracker(course).get("queue", [])}
    queue = queue_cmd(course, "add", section=section.name, core=core, kind=kind, count=count,
                      lens=lens_of(planned) if planned.strip() else "", due=due.strip(),
                      origin=f"{item} ({result})")
    return [i for i in queue if i["id"] not in before]


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
    lg.add_argument("--kind", choices=["harder", "same", "twin"],
                    help="override the follow-up (e.g. same for a hedged correct)")
    lg.add_argument("--answers", help="queue id this question answered; it is closed")
    lg.add_argument("--no-queue", action="store_true", help="log only; queue nothing")
    wk = sub.add_parser("week")
    wk.add_argument("--course", required=True)
    wk.add_argument("--date")
    tr = sub.add_parser("tracker")
    tr.add_argument("action", choices=["show", "set"])
    tr.add_argument("--course", required=True)
    tr.add_argument("pairs", nargs="*", help="key=value, keys: goal goal_date chapters week work")
    qu = sub.add_parser("queue")
    qu.add_argument("action", choices=["add", "tick", "due", "done"])
    qu.add_argument("--course", required=True)
    qu.add_argument("--section")
    qu.add_argument("--core")
    qu.add_argument("--kind", default="twin", help="harder | same | twin")
    qu.add_argument("--count", type=int, default=1)
    qu.add_argument("--gap", type=int, default=3)
    qu.add_argument("--id")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "week":
            print(json.dumps(week_for(args.course, args.date), indent=2))
            return 0
        if args.cmd == "tracker":
            data = tracker_set(args.course, args.pairs) if args.action == "set" else load_tracker(args.course)
            print(json.dumps(data, indent=2))
            return 0
        if args.cmd == "queue":
            if args.action == "add" and not (args.section and args.core):
                raise ValueError("queue add needs --section and --core")
            if args.action == "done" and not args.id:
                raise ValueError("queue done needs --id")
            print(json.dumps(queue_cmd(args.course, args.action, args.section, args.core, args.kind,
                                       args.count, args.gap, args.id), indent=2))
            return 0
        if args.cmd == "scope":
            secs = set(args.sections.split(",")) if args.sections else None
            data = scope(args.kit, chapter_range(args.chapters) if args.chapters else None, secs)
            if not data:
                print("no processed sections match that range")
                return 1
            print(json.dumps(data, indent=2) if args.json else render(data))
        else:
            print(log_attempt(args.section, args.item, args.result, args.reason, args.next_review, args.date), end="")
            if not args.no_queue:
                for i in follow_up(args.section, args.item, args.result, args.next_review, args.kind, args.answers):
                    print(f"queued #{i['id']}: {i['section']} Core {i['core']} · {i['lens'] or i['kind']} "
                          f"({i['kind']}, after {i['gap']} other questions)")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
