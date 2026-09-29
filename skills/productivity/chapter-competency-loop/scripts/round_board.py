#!/usr/bin/env python3
"""Build a competency round board: one question card per answered question.

  round_board.py SPEC.py --work <course>/Week-XX_*/Work
  round_board.py SPEC.py --out FILE

Each card reads top to bottom: the question exactly as asked, the learner's
answer mapped part by part to the correct answer, the reasoning with a picture,
and one line to remember. The open question sits at the top so the learner can
read it on the board and answer in chat. The page is a local file that works
offline; it reuses eli5-explainer's theme tokens and checker (CSP, both themes,
accessible SVGs). Standard library only.
"""
import argparse
import html
import importlib.util
import os
import sys
from pathlib import Path

# eli5-explainer lives beside this skill in the same repository.
ELI5 = Path(__file__).resolve().parents[2] / "eli5-explainer" / "scripts"
sys.path.insert(0, str(ELI5))
import eli5  # noqa: E402
import eli5_page as ep  # noqa: E402

VERDICT = {"correct": "Correct", "partial": "Partly right", "missed": "Not yet"}
MAX_WORDS = 8000  # a board holds a whole round: questions, breakdown steps, and twins
README_HEADING = "## Competency rounds\n"

CSS = ep.CSS + """
.tiles { display: flex; flex-wrap: wrap; gap: 8px; }
.tile { min-width: 3.2em; padding: 8px 12px; border-radius: 10px; text-align: center; text-decoration: none;
  font: 700 0.9rem ui-monospace, "SF Mono", Menlo, monospace; border: 1px solid var(--line);
  background: var(--surface); color: var(--muted); }
.tile.v-correct { background: var(--c3); border-color: var(--c3); color: var(--surface); }
.tile.v-partial { background: var(--c5); border-color: var(--c5); color: var(--surface); }
.tile.v-missed { background: var(--c4); border-color: var(--c4); color: var(--surface); }
.tile.now { border: 2px dashed var(--c1); color: var(--c1); }
.tile:focus-visible { outline: 3px solid var(--c1); outline-offset: 2px; }
.status { color: var(--muted); font-size: 0.95rem; }
.qcard { --v: var(--base); background: var(--surface); border: 1px solid var(--line); border-top: 5px solid var(--v);
  border-radius: 14px; padding: 18px 20px; display: grid; gap: 14px; scroll-margin-top: 80px; }
.qcard.v-correct { --v: var(--c3); } .qcard.v-partial { --v: var(--c5); } .qcard.v-missed { --v: var(--c4); }
.qcard.open { --v: var(--c1); border-style: dashed; border-top-style: solid; }
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
.terms dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 6px 14px; }
.terms dt { font-weight: 700; } .terms dd { margin: 0; }
.context { display: flex; flex-wrap: wrap; gap: 6px 16px; color: var(--muted); font-size: 0.95rem; }
.context b { color: var(--ink); }
details.help { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 12px 18px; }
details.help summary { cursor: pointer; font-weight: 700; }
details.help dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 14px; margin: 12px 0 4px; }
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


def esc(t):
    return html.escape(t, quote=False)


def mapping(parts):
    rows = []
    for label, yours, correct, ok in parts:
        cls, mark = ("ok", "✓") if ok else ("no", "✗")
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
    wide = " wide" if c.get("wide") or not pic else ""  # wide: picture above the text, full card width
    explain = f'<div class="explain{wide}"><div>{pic}</div>'
    return (f'<article class="qcard v-{v}" id="q{n}" data-step="{n}">'
            f'<div class="qhead"><span class="qnum">{esc(label)}</span><span class="meta">{meta}</span>'
            f'<span class="verdict">{VERDICT[v]}</span></div>'
            f'<div class="ask"><div class="label">Question, as asked</div>{c["ask"]}</div>'
            + mapping(c["parts"]) + terms_html(c.get("terms")) +
            f'{explain}<div><div class="label">How to get it</div><p>{c["why"]}</p>'
            f'<div class="remember"><b>Remember:</b> {c["remember"]}</div></div></div>'
            '</article>')


def open_card(n, current):
    return (f'<article class="qcard open" id="now" data-step="{n}">'
            f'<div class="qhead"><span class="qnum">{esc(current.get("num", f"Q{n}"))}</span><span class="meta">{esc(current.get("meta", ""))}</span>'
            '<span class="verdict">Answer in chat</span></div>'
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
    queued = r.get("queued", 0)
    current = r.get("current")
    # Breakdown steps (step=True) get their own tiles and cards but don't count as questions.
    labels, main = [], 0
    for c in cards:
        if not c.get("step"):
            main += 1
        labels.append(c.get("num") or f"Q{main}")
    tiles = [f'<a class="tile v-{c["verdict"]}" href="#q{i + 1}">{esc(labels[i])}</a>' for i, c in enumerate(cards)]
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
    body.extend(card_html(i + 1, c, labels[i]) for i, c in reversed(list(enumerate(cards))))  # newest first
    if len(body) < 2:  # the checker needs two steps
        body.append('<article class="qcard" data-step="2" id="next"><div class="qhead">'
                    '<span class="meta">The next question appears here.</span></div></article>')
    # data-step must run 1..N in document order
    ordered = []
    for k, block in enumerate(body, 1):
        ordered.append(block.replace('data-step="', f'data-step="{k}" data-q="', 1))
    tally = []
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
</header>
{chr(10).join(ordered)}
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
    entry = f"- [`{fname}`]({fname}) — {r['course']} {r['scope']}, round {r['number']} ({r['date']}): one card per answer.\n"
    if README_HEADING not in body:
        body = body.rstrip("\n") + "\n\n" + README_HEADING + "\n" + entry
    else:
        start = body.index(README_HEADING) + len(README_HEADING)
        nxt = body.find("\n## ", start)
        end = len(body) if nxt == -1 else nxt + 1
        rest = body[end:]
        body = body[:start] + body[start:end].rstrip("\n") + "\n" + entry + ("\n" + rest if rest else "")
    readme.write_text(body, encoding="utf-8")


def build(r, work=None, out=None):
    issues = audit(r)
    if issues:
        raise ValueError("board marks contradict their verdicts:\n  " + "\n  ".join(issues))
    text = render(r)
    errors, parsed = eli5.check(text, max_words=MAX_WORDS)
    if errors:
        raise ValueError("board fails eli5 check:\n  " + "\n  ".join(errors))
    if work:
        work = Path(work)
        if not work.is_dir():
            raise ValueError(f"no such Work folder: {work}")
        out = work / f"competency-{r['slug']}.html"
    if out is None:
        raise ValueError("give work (course week folder) or out")
    out = Path(out)
    if out.exists() and "competency round" not in out.read_text(encoding="utf-8"):
        raise ValueError(f"refusing to replace a file that is not a round board: {out}")
    out.write_text(text, encoding="utf-8")
    if work:
        add_readme_line(work, out.name, r)
    return out, f"{len(r['cards'])} cards, {parsed.words} visible words"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a competency round board.")
    ap.add_argument("spec")
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--work", help="the current week's Work folder")
    where.add_argument("--out", help="output .html path")
    args = ap.parse_args(argv)
    try:
        ep.LABEL_WARNINGS.clear()
        r = load_round(args.spec)
        if ep.LABEL_WARNINGS:
            raise ValueError("labels would be clipped:\n  " + "\n  ".join(ep.LABEL_WARNINGS))
        path, summary = build(r, args.work, args.out)
    except (ValueError, KeyError, OSError) as exc:
        print(f"FAIL {exc}")
        return 1
    print(f"OK {path}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
