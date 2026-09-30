#!/usr/bin/env python3
"""Build a competency round board: one question card per answered question.

  round_board.py SPEC.py|RECORD.json --work <course>/Week-XX_*/Work [--course <course dir>]
  round_board.py SPEC.py|RECORD.json --out FILE [--course <course dir>]

Each card reads top to bottom: the question exactly as asked, the learner's
answer mapped part by part to the correct answer, the reasoning with a picture,
and one line to remember. The open question sits at the top so the learner can
read it on the board and answer in chat. The page is a local file that works
offline; it reuses eli5-explainer's theme tokens and checker (CSP, both themes,
accessible SVGs). Standard library only.
"""
import argparse
import copy
import datetime as dt
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

# eli5-explainer lives beside this skill in the same repository.
ELI5 = Path(__file__).resolve().parents[2] / "eli5-explainer" / "scripts"
sys.path.insert(0, str(ELI5))
import eli5  # noqa: E402
import eli5_page as ep  # noqa: E402

VERDICT = {"correct": "Correct", "partial": "Partly right", "missed": "Not yet",
           "unscored": "Not scored"}  # unscored: the question's wording was at fault; teach only
MAX_WORDS = 8000  # a board holds a whole round: questions, breakdown steps, and twins
README_HEADING = "## Competency rounds\n"
RECORDS = ".round-data"  # hidden beside the boards: the JSON records are for the tool, not for reading


def board_name(r):
    """Round 2 - Chapters 1-3 (Sep 29).html: reads like a title and sorts by round in Finder."""
    day = dt.date.fromisoformat(r["date"])
    return f"Round {r['number']} - {r['scope'].replace('–', '-')} ({day.strftime('%b')} {day.day}).html"


def record_path(board):
    board = Path(board)
    return board.parent / RECORDS / (board.stem + ".json")


def board_of(record):
    record = Path(record)
    return record.parent.parent / (record.stem + ".html")


def href(target, from_dir):
    """A relative link that survives the spaces in plain-English file names."""
    return quote(os.path.relpath(target, from_dir))

CSS = ep.CSS + """
.tiles { display: flex; flex-wrap: wrap; gap: 8px; }
.tile { min-width: 3.2em; padding: 8px 12px; border-radius: 10px; text-align: center; text-decoration: none;
  font: 700 0.9rem ui-monospace, "SF Mono", Menlo, monospace; border: 1px solid var(--line);
  background: var(--surface); color: var(--muted); }
.tile.v-correct { background: var(--c3); border-color: var(--c3); color: var(--surface); }
.tile.v-partial { background: var(--c5); border-color: var(--c5); color: var(--surface); }
.tile.v-missed { background: var(--c4); border-color: var(--c4); color: var(--surface); }
.tile.v-unscored { background: var(--bg); color: var(--muted); border-style: dotted; }
.tile.now { border: 2px dashed var(--c1); color: var(--c1); }
.tile.v-moved { background: var(--surface); border: 2px solid var(--c3); color: var(--c3); }
.tile:focus-visible { outline: 3px solid var(--c1); outline-offset: 2px; }
.status { color: var(--muted); font-size: 0.95rem; }
.qcard { --v: var(--base); background: var(--surface); border: 1px solid var(--line); border-top: 5px solid var(--v);
  border-radius: 14px; padding: 18px 20px; display: grid; gap: 14px; scroll-margin-top: 80px; }
.qcard.v-correct { --v: var(--c3); } .qcard.v-partial { --v: var(--c5); } .qcard.v-missed { --v: var(--c4); }
.qcard.open { --v: var(--c1); border-style: dashed; border-top-style: solid; }
.qcard.v-unscored { --v: var(--muted); }
.qcard.is-current { box-shadow: 0 0 0 3px var(--v); }
.qhead { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px; }
.qnum { font: 800 1.1rem ui-monospace, "SF Mono", Menlo, monospace; color: var(--v); }
.meta { color: var(--muted); font-size: 0.9rem; }
.verdict { margin-left: auto; font-weight: 700; color: var(--v); }
.label { font: 600 0.72rem/1 ui-monospace, "SF Mono", Menlo, monospace; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.ask { background: var(--bg); border-radius: 10px; padding: 12px 14px; }
.ask ul { margin: 6px 0 0; padding-left: 1.2em; }
.ask p + p, .ask p + ul { margin-top: 6px; }
.map .tablewrap { overflow-x: auto; }
/* Grid items default to their content's min width; without this a wide answer table
   widens the whole page on a phone. Now the table scrolls inside its own box and words stay whole. */
.wrap > *, .qcard > *, .explain > * { min-width: 0; }
.map td, .map th { overflow-wrap: break-word; }
.next { margin-top: 10px; color: var(--muted); }
.coming { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 14px 18px; }
.coming ul { margin: 0; padding-left: 1.2em; display: grid; gap: 4px; }
.map table { border-collapse: collapse; width: 100%; min-width: 300px; font-variant-numeric: tabular-nums; }
.map th, .map td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
.map th { font-weight: 600; color: var(--muted); font-size: 0.85rem; }
.map td.mark { width: 2em; text-align: center; font-weight: 800; }
.map tr.ok td.mark { color: var(--c3); } .map tr.no td.mark { color: var(--c4); }
.map tr.no td.yours { color: var(--c4); text-decoration: line-through; text-decoration-color: var(--c4); }
.map td.correct { font-weight: 700; }
.explain { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; align-items: center; }
.explain.wide { grid-template-columns: 1fr; }
.explain p { max-width: 60ch; }
.remember { border-left: 4px solid var(--v); padding: 6px 12px; background: var(--bg); border-radius: 0 8px 8px 0; margin-top: 10px; }
.terms { background: var(--bg); border-radius: 10px; padding: 10px 14px; }
.terms dl { margin: 0; display: grid; grid-template-columns: fit-content(40%) 1fr; gap: 6px 14px; }
.terms dt { font-weight: 700; } .terms dd { margin: 0; }
.context { display: flex; flex-wrap: wrap; gap: 6px 16px; color: var(--muted); font-size: 0.95rem; }
.context b { color: var(--ink); }
details.help { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px 18px; }
details.help summary { cursor: pointer; font-weight: 700; }
/* fit-content caps the term column so a long command wraps instead of pushing the page sideways on a phone */
details.help dl { display: grid; grid-template-columns: fit-content(40%) 1fr; gap: 6px 14px; margin: 12px 0 4px; }
.terms dt, details.help dt { overflow-wrap: anywhere; }
details.help dt { font: 600 0.9rem ui-monospace, "SF Mono", Menlo, monospace; } details.help dd { margin: 0; }
.tally { display: grid; gap: 8px; }
.tally div { display: grid; grid-template-columns: 7.5em 1fr 2em; align-items: center; gap: 10px; }
.tally span.bar-fill { display: block; height: 18px; border-radius: 4px; }
@media (max-width: 720px) { .explain { grid-template-columns: 1fr; } .verdict { margin-left: 0; } }
"""


HELP = [("help", "show this menu in chat"), ("status", "tracker and each concept's status"),
        ("set goal / set exam date / set chapters / set week", "change the tracker (confirmed first)"),
        ("move files to week N", "relocate this round's files (confirmed first)"),
        ("hint", "next hint for the open question"), ("explain", "teach it now, then continue"),
        ("easier / harder", "change the next question's difficulty"), ("skip", "queue the open question unscored"),
        ("fix log …", "correct a logged result (confirmed first)"), ("end round", "close with the summary")]


KIND = {"harder": "harder", "same": "same level", "twin": "new scenario", "bug hunt": "mastery check"}


def queue_html(queue):
    """Every re-check waiting in the tracker, so a correct answer visibly comes back too."""
    if not queue:
        return ""
    rows = []
    for i in queue:
        left = i["gap"] - i["since"]
        when = "ready now" if left <= 0 else f"after {left} more question{'s' if left != 1 else ''}"
        what = i.get("lens") or "re-check"
        due = f" · review by {i['due']}" if i.get("due") else ""
        title = f" {esc(i['title'])}" if i.get("title") else ""
        rows.append(f"<li><b>{esc(i['section'])} Core {i['core']}{title}</b> · {esc(what)} "
                    f"<span class=\"meta\">({KIND.get(i['kind'], i['kind'])}, {when}{esc(due)})</span></li>")
    return (f'<section class="coming"><div class="label">Coming back ({len(queue)})</div>'
            f'<ul>{"".join(rows)}</ul></section>')


def esc(t):
    return html.escape(t, quote=False)


def mapping(parts, graded=True):
    rows = []
    for label, yours, correct, ok in parts:
        cls, mark = (("ok", "✓") if ok else ("no", "✗")) if graded else ("", "")
        rows.append(f'<tr class="{cls}"><td>{esc(label)}</td><td class="yours">{esc(yours or "—")}</td>'
                    f'<td class="correct">{esc(correct)}</td><td class="mark" aria-label="{"right" if ok else "wrong"}">{mark}</td></tr>')
    return ('<div class="map"><div class="label">Your answer → correct answer</div><div class="tablewrap"><table>'
            '<tr><th>Part</th><th>You said</th><th>Correct</th><th></th></tr>' + "".join(rows) + '</table></div></div>')


def terms_html(terms):
    """The key words the question or explanation relies on, defined plainly."""
    if not terms:
        return ""
    items = "".join(f"<dt>{esc(t)}</dt><dd>{d}</dd>" for t, d in terms)
    return f'<div class="terms"><div class="label">Words used here</div><dl>{items}</dl></div>'


def card_html(n, c, label):
    v = c["verdict"]
    meta = f"{esc(c['section'])} · {esc(c['concept'])} · {esc(c['lens'])}"
    pic = c.get("svg", "")
    # wide: picture above the text at full card width. Only for genuinely wide drawings
    # (viewBox wider than 420); a normal 360-wide picture stretched full width looks giant.
    vb = re.search(r'viewBox="0 0 ([\d.]+) ', pic or "")
    is_wide = bool(vb) and float(vb.group(1)) > 420
    wide = " wide" if (c.get("wide") and is_wide) or not pic else ""
    explain = f'<div class="explain{wide}"><div>{pic}</div>'
    return (f'<article class="qcard v-{v}" id="q{n}" data-step="{n}">'
            f'<div class="qhead"><span class="qnum">{esc(label)}</span><span class="meta">{meta}</span>'
            f'<span class="verdict">{VERDICT[v]}</span></div>'
            f'<div class="ask"><div class="label">Question, as asked</div>{c["ask"]}</div>'
            + mapping(c["parts"], graded=v != "unscored") + terms_html(c.get("terms")) +
            f'{explain}<div><div class="label">How to get it</div><p>{c["why"]}</p>'
            f'<div class="remember"><b>Remember:</b> {c["remember"]}</div>'
            + (f'<p class="next"><b>Comes back as:</b> {esc(c["next"])}</p>' if c.get("next") else "")
            + '</div></div></article>')


def link_list(links):
    return ", ".join(f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in links)


def review_html(groups):
    """The cue at a round's start: per topic coming back this round, the earlier cards that teach it."""
    if not groups:
        return ""
    items = "".join(f"<li><b>{esc(topic)}</b>: {link_list(links)}</li>" for topic, links in groups)
    return ('<section class="coming"><div class="label">Review before this round</div>'
            "<p>These topics come back as re-checks this round. Read their cards first; the re-checks "
            "use new scenarios and numbers, so reviewing won't give the answers away.</p>"
            f"<ul>{items}</ul></section>")


def open_card(n, current):
    recheck = current.get("review_links")
    cue = (f'<p class="meta">Re-check: review {link_list(recheck)} first, then answer.</p>' if recheck else "")
    return (f'<article class="qcard open" id="now" data-step="{n}">'
            f'<div class="qhead"><span class="qnum">{esc(current.get("num", f"Q{n}"))}</span><span class="meta">{esc(current.get("meta", ""))}</span>'
            '<span class="verdict">Answer in chat</span></div>' + cue
            + terms_html(current.get("terms")) +
            f'<div class="ask"><div class="label">Question, as asked</div>{current["ask"]}</div></article>')


def context_html(ctx):
    """What this round is for and where it is saved, from the tracker."""
    if not ctx:
        return ""
    bits = [f"<span>{esc(k)}: <b>{esc(str(v))}</b></span>" for k, v in ctx.items() if v]
    return f'<div class="context">{"".join(bits)}</div>'


def render(r):
    cards = r["cards"]
    planned = r.get("planned", len(cards))
    queued = len(r["queue"]) if "queue" in r else r.get("queued", 0)
    current = r.get("current")
    # Breakdown steps (step=True) get their own tiles and cards but don't count as questions.
    labels, main = [], 0
    for c in cards:
        if not c.get("step"):
            main += 1
        labels.append(c.get("num") or f"Q{main}")
    # A card whose topics are all mastered lives in its chapter's mastery file; its tile links there.
    tiles = [f'<a class="tile v-moved" href="{esc(c["moved_to"])}" title="moved to chapter mastery">{esc(labels[i])} ✓</a>'
             if c.get("moved_to") else
             f'<a class="tile v-{c["verdict"]}" href="#q{i + 1}">{esc(labels[i])}</a>' for i, c in enumerate(cards)]
    nxt = main + 1
    if current:
        tiles.append(f'<a class="tile now" href="#now">{esc(current.get("num", f"Q{nxt}"))}</a>')
        if not current.get("step"):
            nxt += 1
    tiles.extend(f'<span class="tile">Q{k}</span>' for k in range(nxt, planned + 1))
    mains = [c for c in cards if not c.get("step")]
    got = sum(c["verdict"] == "correct" for c in mains)
    waiting = f" · {queued} re-check{'s' if queued != 1 else ''} coming later" if queued else ""
    body = []
    if current:
        body.append(open_card(main + 1, current))
    body.extend(card_html(i + 1, c, labels[i]) for i, c in reversed(list(enumerate(cards)))
                if not c.get("moved_to"))  # newest first
    pages = sorted({c["moved_to"].split("#")[0] for c in cards if c.get("moved_to")})
    moved = sum(bool(c.get("moved_to")) for c in cards)
    moved_note = (f'<p class="status">✓ {moved} card{"s" if moved != 1 else ""} for mastered topics moved to '
                  + ", ".join(f'<a href="{esc(pg)}">{esc(unquote(Path(pg).stem))}</a>' for pg in pages)
                  + '. Everything still here is for review.</p>') if moved else ""
    if len(body) < 2:  # the checker needs two steps
        body.append('<article class="qcard" data-step="2" id="next"><div class="qhead">'
                    '<span class="meta">The next question appears here.</span></div></article>')
    # data-step must run 1..N in document order
    ordered = []
    for k, block in enumerate(body, 1):
        ordered.append(block.replace('data-step="', f'data-step="{k}" data-q="', 1))
    tally = []
    mains = [c for c in mains if c["verdict"] != "unscored"]
    for v, k in (("correct", "c3"), ("partial", "c5"), ("missed", "c4")):
        n = sum(c["verdict"] == v for c in mains)
        pct = 0 if not mains else 100 * n / len(mains)
        tally.append(f'<div><span>{VERDICT[v]}</span><span><span class="bar-fill" style="width:{pct:.0f}%;background:var(--{k})"></span></span><span>{n}</span></div>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{ep.CSP}">
<title>{esc(r['course'])} Round {r['number']}</title>
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
  <span class="tag">{esc(r['course'])} · {esc(r['scope'])} · competency round {r['number']} · {esc(r['date'])}</span>
  <h1>Round {r['number']}</h1>
  {context_html(r.get("context"))}
  <nav class="tiles" aria-label="Jump to a question">{"".join(tiles)}</nav>
  <p class="status">{got} correct of {len(mains)} answered · {planned} planned{waiting}. Tap a tile to jump to its card; the newest card is first.</p>
  {moved_note}
</header>
{review_html(r.get("review_links"))}
{chr(10).join(ordered)}
{queue_html(r.get("queue"))}
<details class="help"><summary>Help menu: type any of these in chat</summary><dl>{"".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in HELP)}</dl></details>
<section class="recap"><span class="tag">Round tally</span><div class="tally">{"".join(tally)}</div></section>
<footer><span>Questions come from the {esc(r['course'])} kit's Core notes for {esc(r['scope'])}. Every result is logged in that section's study-log.md.</span></footer>
</main>
<script>{ep.JS}</script>
</body>
</html>
"""


def audit(r):
    """Marks must agree with verdicts, so a card never tells an unsure learner the wrong thing."""
    issues = []
    for i, c in enumerate(r["cards"], 1):
        parts, v = c.get("parts", []), c["verdict"]
        name = c.get("num") or f"card {i}"
        cores = c.get("cores")
        if not cores or not all(isinstance(k, int) for k in cores):
            # the topics a card teaches; mastery.py moves it once they're all covered
            issues.append(f"{name}: no 'cores' (the Core numbers it covers in its section)")
        if v == "unscored":
            continue  # a teaching card with no grade; its marks are not a verdict
        if not c.get("step") and not c.get("next"):
            # every scored answer, right or wrong, comes back as a re-check
            issues.append(f"{name}: no 'next' (the re-check it comes back as)")
        if not parts:
            issues.append(f"{name}: no answer rows")
            continue
        first_ok = parts[0][3]
        if v == "correct" and not all(p[3] for p in parts if not p[0].startswith("Extra")):
            issues.append(f"{name}: verdict 'correct' but a non-extra row is marked wrong")
        if v == "missed" and first_ok:
            issues.append(f"{name}: verdict 'missed' but the direct-answer row (first) is marked right")
        if v == "correct" and not first_ok:
            issues.append(f"{name}: verdict 'correct' but the direct-answer row (first) is marked wrong")
        for label, yours, correct, ok in parts:
            if ok and not (yours or "").strip():
                issues.append(f"{name}: '{label}' is marked right but the learner's answer is blank")
            if not ok and (yours or "").strip().lower() == correct.strip().lower():
                issues.append(f"{name}: '{label}' is marked wrong but matches the correct answer")
        if parts[0][0].startswith("Extra"):
            issues.append(f"{name}: the first row must answer the question itself, not an extra")
    return issues


def load_round(spec_path):
    """A Python spec (authoring) or the JSON record a build saved beside its board."""
    if str(spec_path).endswith(".json"):
        return json.loads(Path(spec_path).read_text(encoding="utf-8"))
    sys.path.insert(0, os.path.dirname(os.path.abspath(spec_path)))
    spec = importlib.util.spec_from_file_location("round_spec", spec_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load spec {spec_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ROUND


def add_readme_line(work, fname, r):
    readme = work / "README.md"
    # A new README gets a title naming its week folder, like the kit's own Work READMEs.
    body = readme.read_text(encoding="utf-8") if readme.is_file() else f"# {work.parent.name} Work\n"
    if fname in body:
        return
    entry = f"- [{fname}]({quote(fname)}) — {r['course']} {r['scope']}, round {r['number']} ({r['date']}): one card per answer.\n"
    if README_HEADING not in body:
        body = body.rstrip("\n") + "\n\n" + README_HEADING + "\n" + entry
    else:
        start = body.index(README_HEADING) + len(README_HEADING)
        nxt = body.find("\n## ", start)
        end = len(body) if nxt == -1 else nxt + 1
        rest = body[end:]
        body = body[:start] + body[start:end].rstrip("\n") + "\n" + entry + ("\n" + rest if rest else "")
    readme.write_text(body, encoding="utf-8")


def number_cards(r):
    """Fix each card's label (Q3, Q2 · step 1) so it survives cards moving off the board."""
    main = 0
    for c in r["cards"]:
        if not c.get("step"):
            main += 1
        c.setdefault("num", f"Q{main}")


def write_board(r, out):
    """Audit, render, check, and write one board; returns the visible word count."""
    issues = audit(r)
    if issues:
        raise ValueError("board fails its audit:\n  " + "\n  ".join(issues))
    text = render(r)
    errors, parsed = eli5.check(text, max_words=MAX_WORDS)
    if errors:
        raise ValueError("board fails eli5 check:\n  " + "\n  ".join(errors))
    out = Path(out)
    if out.exists() and "competency round" not in out.read_text(encoding="utf-8"):
        raise ValueError(f"refusing to replace a file that is not a round board: {out}")
    out.write_text(text, encoding="utf-8")
    return parsed.words


def save_record(r, out):
    """The round's cards as JSON beside the board: the lasting record mastery.py reads."""
    rec = copy.deepcopy({k: v for k, v in r.items() if k not in ("queue", "review_links")})
    if rec.get("current"):
        rec["current"].pop("review_links", None)  # derived from the records on every build
    for c in rec["cards"]:
        c.pop("moved_to", None)
    path = record_path(out)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def build(r, work=None, out=None):
    r = copy.deepcopy(r)  # numbering the cards must not change the caller's spec
    number_cards(r)
    if work:
        work = Path(work)
        if not work.is_dir():
            raise ValueError(f"no such Work folder: {work}")
        out = work / board_name(r)
    if out is None:
        raise ValueError("give work (course week folder) or out")
    words = write_board(r, out)
    save_record(r, out)
    if work:
        add_readme_line(work, Path(out).name, r)
    return Path(out), f"{len(r['cards'])} cards, {words} visible words"


def find_cards(course, section, core):
    """Every saved card, in any round, that teaches this topic: (round, label, board, anchor)."""
    out = []
    for rec in sorted(Path(course).glob(f"Week*/Work/{RECORDS}/*.json")):
        r = load_round(rec)
        for i, c in enumerate(r["cards"], 1):
            if c.get("section") == section and core in (c.get("cores") or []):
                out.append((r["number"], c.get("num", f"card {i}"), board_of(rec), f"q{i}"))
    return out


def attach_review(r, course, board_dir):
    """Resolve review cues to links: the round's `review` topics and the open question's `recheck` topic.

    Topics are (section, core) pairs, so a spec never hard-codes where earlier cards live.
    """
    def links(topics):
        seen, out = set(), []
        for section, core in topics:
            for number, label, board, anchor in find_cards(course, section, core):
                if (board, anchor) not in seen and number != r["number"]:
                    seen.add((board, anchor))
                    out.append((f"Round {number} · {label}", href(board, board_dir) + "#" + anchor))
        return out
    # One line per section's set of cards, naming every topic those cards teach.
    import competency
    groups = {}
    for section, core in (tuple(t) for t in r.get("review", [])):
        found = list((Path(course) / "Chapter-Kits").glob(f"Chapter-*/{section}"))
        title = dict(competency.core_concepts(found[0])).get(core, f"Core {core}") if found else f"Core {core}"
        got = links([(section, core)])
        if got:
            groups.setdefault((section, tuple(got)), []).append(title)
    r["review_links"] = [(f"{section} " + ", ".join(names), list(got)) for (section, got), names in groups.items()]
    if r.get("current") and r["current"].get("recheck"):
        r["current"]["review_links"] = links([tuple(r["current"]["recheck"])])


def attach_queue(r, course):
    """Read the re-check queue from the tracker so the board can't drift from it."""
    tracker = Path(course) / "competency-tracker.json"
    if tracker.is_file():
        r["queue"] = json.loads(tracker.read_text(encoding="utf-8")).get("queue", [])
        name_concepts(Path(course), r["queue"])


def name_concepts(course, queue):
    """Give each queued re-check its Core heading, so the board names the idea, not just a number."""
    import competency
    for i in queue:
        found = list((course / "Chapter-Kits").glob(f"Chapter-*/{i.get('section')}"))
        if found:
            i["title"] = dict(competency.core_concepts(found[0])).get(i.get("core"), "")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a competency round board.")
    ap.add_argument("spec")
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--work", help="the current week's Work folder")
    where.add_argument("--out", help="output .html path")
    ap.add_argument("--course", help="course folder: reads the re-check queue from its tracker, then runs mastery sync")
    args = ap.parse_args(argv)
    try:
        ep.LABEL_WARNINGS.clear()
        r = load_round(args.spec)
        if args.course:
            attach_queue(r, args.course)
            attach_review(r, args.course, Path(args.work) if args.work else Path(args.out).parent)
        if ep.LABEL_WARNINGS:
            raise ValueError("labels would be clipped:\n  " + "\n  ".join(ep.LABEL_WARNINGS))
        path, summary = build(r, args.work, args.out)
        if args.course:
            # Move cards for mastered topics off every board and into the chapter mastery files.
            import mastery
            for line in mastery.sync(args.course):
                print(f"  {line}")
    except (ValueError, KeyError, OSError) as exc:
        print(f"FAIL {exc}")
        return 1
    print(f"OK {path}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
