#!/usr/bin/env python3
"""Move mastered topics' cards off the round boards into per-chapter mastery files.

  mastery.py sync --course <course dir>

A topic (one numbered Core concept of a section) is mastered when competency.py
says it is covered: competency shown, then its bug hunt passed. Each round
board's JSON record, saved beside it by round_board.py, lists every card and
the Core numbers it teaches (`cores`). Sync reads every record in the course's
week Work folders and:

- marks a card as moved when all of its topics are covered, and rebuilds that
  round's board without it (its tile links to the card's new home);
- writes <course>/Mastery/chapter-NN-mastery.html for each chapter with a
  mastered topic: the chapter's sections, each mastered topic, and its cards;
- lists the chapter files in <course>/Mastery/README.md.

Nothing is deleted. The JSON records keep every card, so a topic that loses
coverage (two missed bug hunts) goes back to its round board on the next sync.
Standard library only.
"""
import argparse
import html
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import competency as comp  # noqa: E402
import round_board as rb  # noqa: E402

ep, eli5 = rb.ep, rb.eli5
MAX_WORDS = 60000  # a chapter file grows to hold every mastered topic's cards
MARKER = "chapter mastery"
CSS = rb.CSS + """
.progress { height: 10px; border-radius: 99px; background: var(--line); overflow: hidden; }
.progress i { display: block; height: 100%; background: var(--c3); }
"""


def esc(t):
    return html.escape(str(t), quote=False)


def topics(course):
    """(section, core) -> status, topic title, section title, and the date it was covered."""
    out = {}
    for sec in comp.scope(Path(course) / "Chapter-Kits"):
        path = Path(sec["path"])
        for c in sec["concepts"]:
            rows = comp.concept_rows(path, c["core"])
            out[(sec["section"], c["core"])] = dict(status=c["status"], title=c["title"],
                                                    section_title=sec["title"],
                                                    date=rows[-1]["date"] if rows else "")
    return out


def anchor(r, c):
    return f"r{r['number']}-" + re.sub(r"[^a-z0-9]+", "-", c["num"].lower()).strip("-")


def page_for(course, chapter):
    return Path(course) / "Mastery" / f"chapter-{chapter:02d}-mastery.html"


def records(course):
    return sorted(Path(course).glob("Week*/Work/competency-*.json"))


def render_chapter(course_name, chapter, items, tops):
    """items: (round, card) pairs whose topics are all covered, for one chapter."""
    in_chapter = {k: v for k, v in tops.items() if k[0].split(".")[0] == str(chapter)}
    covered = {k: v for k, v in in_chapter.items() if v["status"] == "covered"}
    sections = sorted({k[0] for k in covered}, key=lambda s: [int(x) for x in s.split(".")])
    blocks, n = [], 0
    for sid in sections:
        mine = sorted((k for k in covered if k[0] == sid), key=lambda k: k[1])
        head = in_chapter[mine[0]]["section_title"]
        listed = "".join(f"<li><b>Core {k[1]}</b> {esc(covered[k]['title'])} "
                         f"<span class=\"meta\">(mastered {esc(covered[k]['date'])})</span></li>" for k in mine)
        cards = sorted((rc for rc in items if rc[1]["section"] == sid),
                       key=lambda rc: (min(rc[1]["cores"]), rc[0]["number"], rc[0]["cards"].index(rc[1])))
        html_cards = []
        for r, c in cards:
            n += 1
            label = f"R{r['number']} · {c['num']}"
            html_cards.append(f'<div id="{anchor(r, c)}">' + rb.card_html(n, c, label) + "</div>")
        blocks.append(f'<section class="coming"><div class="label">{esc(sid)} {esc(head)}</div>'
                      f"<ul>{listed}</ul></section>" + "".join(html_cards))
    if n == 0:  # coverage was lost: say so rather than leave stale cards
        blocks.append('<article class="qcard" data-step="1"><div class="qhead"><span class="meta">'
                      "No topic in this chapter is mastered right now; its cards are back on the round boards.</span></div></article>")
    if n < 2:  # the checker needs two steps
        blocks.append('<article class="qcard" data-step="2"><div class="qhead"><span class="meta">'
                      "More mastered topics appear here as their bug hunts pass.</span></div></article>")
    # data-step must run 1..N in document order
    body, k = "\n".join(blocks), 0

    def step(_):
        nonlocal k
        k += 1
        return f'data-step="{k}" data-q="'
    body = re.sub(r'data-step="', step, body)
    total, done = len(in_chapter), len(covered)
    pct = 0 if not total else 100 * done / total
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{ep.CSP}">
<title>{esc(course_name)} Chapter {chapter} Mastery</title>
<style>{CSS}</style>
</head>
<body>
<div class="bar" id="bar" hidden>
  <button type="button" class="primary" id="play">Play</button>
  <button type="button" id="back" aria-label="Previous card">Back</button>
  <button type="button" id="next" aria-label="Next card">Next</button>
  <span class="where" id="where" aria-live="polite">Card 1</span>
  <div class="track" aria-hidden="true"><i id="fill"></i></div>
</div>
<main class="wrap">
<header class="hero">
  <span class="tag">{esc(course_name)} · chapter {chapter} · {MARKER}</span>
  <h1>Chapter {chapter} mastery</h1>
  <p class="status"><b>{done} of {total}</b> topics mastered</p>
  <div class="progress" aria-hidden="true"><i style="width:{pct:.0f}%"></i></div>
  <p class="status">Each topic here passed its competency check and its bug hunt. The cards are the proof and the notes: the question, your answer, and how to get it. Topics not listed yet stay on the round boards for review.</p>
</header>
{body}
</main>
<script>{ep.JS}</script>
</body>
</html>
"""


def write_readme(course, pages, tops):
    lines = [f"# {Path(course).name} mastery", "",
             "One file per chapter. A topic appears once it passes its competency check and its bug hunt;",
             "the rest stay on the round boards in the week Work folders.", ""]
    for chapter, page in pages:
        in_ch = [v for k, v in tops.items() if k[0].split(".")[0] == str(chapter)]
        done = sum(v["status"] == "covered" for v in in_ch)
        lines.append(f"- [`{page.name}`]({page.name}) — chapter {chapter}: {done} of {len(in_ch)} topics mastered.")
    (Path(course) / "Mastery" / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync(course):
    """Move covered topics' cards; rebuild the boards and chapter files. Returns a summary."""
    course = Path(course)
    tops = topics(course)
    chapters, summary = {}, []
    for rec in records(course):
        r = rb.load_round(rec)
        moved = 0
        for c in r["cards"]:
            c.pop("moved_to", None)
            cores = c.get("cores") or []
            if cores and all(tops.get((c["section"], k), {}).get("status") == "covered" for k in cores):
                chapter = int(c["section"].split(".")[0])
                c["moved_to"] = os.path.relpath(page_for(course, chapter), rec.parent) + "#" + anchor(r, c)
                chapters.setdefault(chapter, []).append((r, c))
                moved += 1
        rb.attach_queue(r, course)
        rb.write_board(r, rec.with_suffix(".html"))
        summary.append(f"{rec.with_suffix('.html').name}: {moved} card(s) moved, {len(r['cards']) - moved} kept")
    # Chapters that had a file but lost every mastered card still get rewritten, so nothing stale remains.
    existing = {int(m.group(1)) for p in (course / "Mastery").glob("chapter-*-mastery.html")
                if (m := re.match(r"chapter-(\d+)-mastery", p.stem))}
    pages = []
    for chapter in sorted(set(chapters) | existing):
        page = page_for(course, chapter)
        text = render_chapter(course.name, chapter, chapters.get(chapter, []), tops)
        errors, _ = eli5.check(text, max_words=MAX_WORDS)
        if errors:
            raise ValueError(f"{page.name} fails eli5 check:\n  " + "\n  ".join(errors))
        if page.exists() and MARKER not in page.read_text(encoding="utf-8"):
            raise ValueError(f"refusing to replace a file that is not a mastery page: {page}")
        page.parent.mkdir(exist_ok=True)
        page.write_text(text, encoding="utf-8")
        pages.append((chapter, page))
        summary.append(f"{page.name}: {len(chapters.get(chapter, []))} card(s)")
    if pages:
        write_readme(course, pages, tops)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description="Move mastered topics' cards into chapter mastery files.")
    ap.add_argument("action", choices=["sync"])
    ap.add_argument("--course", required=True)
    args = ap.parse_args(argv)
    try:
        for line in sync(args.course):
            print(line)
    except (ValueError, KeyError, OSError) as exc:
        print(f"FAIL {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
