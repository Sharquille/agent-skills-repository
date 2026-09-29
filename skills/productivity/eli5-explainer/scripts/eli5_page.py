#!/usr/bin/env python3
"""Build an ELI5 page from a spec module in the shared page shell.

  eli5_page.py SPEC.py --root TERM_DIR   course topic -> <course>/Week-XX_*/Work/
  eli5_page.py SPEC.py --out FILE        any other topic

A spec is a Python file that imports the SVG helpers below
(`from eli5_page import svg, box, text, arrow, line, person`) and defines PAGE.
The page is checked with eli5.check before anything is written. Standard library only.
"""
import argparse
import html
import importlib.util
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eli5  # noqa: E402

# ---------- SVG helpers for specs ----------


def esc(t):
    return html.escape(t, quote=False)


def text(x, y, s, cls="", anchor="middle", extra=""):
    c = f' class="{cls}"' if cls else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x}" y="{y}"{c}{a}{extra}>{esc(s)}</text>'


# Labels estimated wider than their box. A clipped label misleads a reader, so
# builders report these: the round board refuses to build, ELI5 pages warn.
LABEL_WARNINGS = []


def box(x, y, w, h, lines, cls="card", tcls="", r=8, lh=16):
    """Rect with centered lines of text. Use cls "fill k2" with tcls "on" for a colored box."""
    if isinstance(lines, str):
        lines = [lines]
    per_char = 6.0 if "sm" in tcls.split() else 7.2  # 11px vs 13px, weight 600
    for ln in lines:
        if len(ln) * per_char > w - 6:
            LABEL_WARNINGS.append(f"label '{ln}' (~{len(ln) * per_char:.0f}px) is wider than its {w}px box")
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>']
    top = y + h / 2 - (len(lines) - 1) * lh / 2 + 5
    for i, ln in enumerate(lines):
        out.append(text(x + w / 2, round(top + i * lh, 1), ln, tcls))
    return "".join(out)


def arrow(x1, y1, x2, y2, cls="ln"):
    ang = math.atan2(y2 - y1, x2 - x1)
    heads = [(x2 + 8 * math.cos(ang + d), y2 + 8 * math.sin(ang + d)) for d in (math.radians(150), -math.radians(150))]
    (hx1, hy1), (hx2, hy2) = heads
    return (f'<path class="{cls}" d="M{x1} {y1} L{x2} {y2} M{hx1:.1f} {hy1:.1f} '
            f'L{x2} {y2} L{hx2:.1f} {hy2:.1f}"/>')


def line(x1, y1, x2, y2, cls="thin"):
    return f'<path class="{cls}" d="M{x1} {y1} L{x2} {y2}"/>'


def person(x, y, w=40, h=90, cls="k0"):
    return f'<use href="#person" x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>'


TEXT_RE = re.compile(r'<text x="([-\d.]+)" y="[-\d.]+"(?: class="([^"]*)")?(?: text-anchor="(\w+)")?[^>]*>([^<]*)</text>')


def svg(inner, label, vb="0 0 360 230"):
    # Free-standing labels that would run past the picture's left or right edge get clipped.
    width = float(vb.split()[2])
    for x, cls, anchor, content in TEXT_RE.findall(inner):
        w = len(html.unescape(content)) * (6.0 if "sm" in (cls or "").split() else 7.2)
        left = float(x) - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
        if left < -2 or left + w > width + 2:
            LABEL_WARNINGS.append(f"label '{html.unescape(content)}' runs past the picture's edge (x {left:.0f} to {left + w:.0f}, width {width:.0f})")
    return (f'<svg class="fig" viewBox="{vb}" role="img" aria-label="{html.escape(label)}">'
            f'{inner}</svg>')

# ---------- page shell ----------

CSP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
       "img-src data:; base-uri 'none'; form-action 'none'")

# Five category colors (--c1..--c5): pick one per recurring category and keep it.
# Step classes s1..s5 tint a step; SVG classes k0..k5/km color shapes via currentColor.
CSS = """
:root {
  --bg: #F2F4F8; --surface: #FFFFFF; --ink: #18202C; --muted: #5A6476; --line: #D3DAE5;
  --c1: #2F6FDE; --c2: #8A4ED4; --c3: #0B8A7C; --c4: #D13D64; --c5: #B0730A; --base: #4A5568;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0F131A; --surface: #171C26; --ink: #E7EBF2; --muted: #9AA4B6; --line: #2A3242;
    --c1: #74A0F2; --c2: #B690F2; --c3: #3FC4B2; --c4: #F27A98; --c5: #E4AE48; --base: #AEB8C8;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0F131A; --surface: #171C26; --ink: #E7EBF2; --muted: #9AA4B6; --line: #2A3242;
  --c1: #74A0F2; --c2: #B690F2; --c3: #3FC4B2; --c4: #F27A98; --c5: #E4AE48; --base: #AEB8C8;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 17px/1.55 "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif; }
.wrap { max-width: 980px; margin: 0 auto; padding: 0 16px 64px; display: grid; gap: 28px; }
h1, h2 { text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: clamp(2rem, 5vw, 3.1rem); font-weight: 800; letter-spacing: -0.02em; }
h2 { font-size: 1.45rem; font-weight: 750; }
p { margin: 0; max-width: 60ch; }
code { font: 0.9em ui-monospace, "SF Mono", Menlo, monospace; }
.tag { font: 600 0.72rem/1 ui-monospace, "SF Mono", Menlo, monospace;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 2;
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 16px; background: var(--bg); border-bottom: 1px solid var(--line); }
.bar button { font: 600 0.9rem/1 inherit; color: var(--ink); background: var(--surface);
  border: 1px solid var(--line); border-radius: 999px; padding: 9px 16px; cursor: pointer; }
.bar button.primary { background: var(--ink); color: var(--bg); border-color: var(--ink); }
.bar button:focus-visible { outline: 3px solid var(--c1); outline-offset: 2px; }
.bar .where { margin-left: auto; font: 600 0.85rem/1 ui-monospace, "SF Mono", Menlo, monospace; color: var(--muted); }
.track { flex-basis: 100%; height: 4px; background: var(--line); border-radius: 2px; overflow: hidden; }
.track i { display: block; height: 100%; width: 100%; background: var(--ink); transform-origin: left;
  transform: scaleX(0); transition: transform .4s ease; }
.hero { display: grid; gap: 18px; padding-top: 36px; }
.hero p { font-size: 1.15rem; color: var(--muted); }
.step { --c: var(--base); display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 24px; align-items: center; padding: 22px; background: var(--surface);
  border: 1px solid var(--line); border-radius: 14px; transition: box-shadow .3s ease, border-color .3s ease; }
.step.is-current { border-color: var(--c); box-shadow: 0 0 0 3px var(--c); }
.step .copy { display: grid; gap: 10px; }
.step .num { font: 700 0.8rem/1 ui-monospace, "SF Mono", Menlo, monospace; color: var(--c); letter-spacing: 0.06em; }
.step b { color: var(--c); }
.s1 { --c: var(--c1); } .s2 { --c: var(--c2); } .s3 { --c: var(--c3); } .s4 { --c: var(--c4); } .s5 { --c: var(--c5); }
.analogy { font-size: 0.92rem; color: var(--muted); }
svg.fig { width: 100%; height: auto; display: block; }
.fig text { font: 600 13px "Avenir Next", "Segoe UI", system-ui, sans-serif; fill: var(--ink); }
.fig .sm { font-size: 11px; fill: var(--muted); font-weight: 500; }
.fig .big { font-size: 20px; font-weight: 800; }
.fig .on { fill: var(--surface); }
.fig .ln { fill: none; stroke: var(--ink); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.fig .thin { fill: none; stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 4 4; }
.fig .axis { fill: none; stroke: var(--muted); stroke-width: 1.5; }
.fig .card { fill: var(--bg); stroke: var(--line); stroke-width: 1.5; }
.fig .solid { fill: var(--surface); stroke: var(--ink); stroke-width: 2.5; }
.fig .fill { fill: currentColor; stroke: none; }
.fig .cs { fill: none; stroke: currentColor; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.fig .soft { fill: currentColor; opacity: .18; stroke: currentColor; stroke-width: 1.5; }
.k0 { color: var(--ink); } .k1 { color: var(--c1); } .k2 { color: var(--c2); } .k3 { color: var(--c3); }
.k4 { color: var(--c4); } .k5 { color: var(--c5); } .km { color: var(--muted); }
.recap { padding: 22px; background: var(--surface); border: 1px solid var(--line); border-radius: 14px; display: grid; gap: 12px; }
footer { color: var(--muted); font-size: 0.9rem; display: grid; gap: 6px; }
@media (max-width: 720px) { .step { grid-template-columns: 1fr; padding: 16px; } body { font-size: 16px; } }
@media (prefers-reduced-motion: reduce) { .track i, .step { transition: none; } }
"""

JS = """
(() => {
  const steps = Array.from(document.querySelectorAll("[data-step]"));
  const bar = document.getElementById("bar");
  const play = document.getElementById("play");
  const where = document.getElementById("where");
  const fill = document.getElementById("fill");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const HOLD_MS = 9000;
  let i = -1;
  let timer = null;
  function go(n) {
    i = Math.max(0, Math.min(steps.length - 1, n));
    steps.forEach((s, k) => s.classList.toggle("is-current", k === i));
    steps[i].scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
    where.textContent = `Step ${i + 1} of ${steps.length}`;
    fill.style.transform = `scaleX(${(i + 1) / steps.length})`;
  }
  function stop() { clearInterval(timer); timer = null; play.textContent = "Play"; }
  function start() {
    if (i >= steps.length - 1 || i < 0) go(0);
    play.textContent = "Pause";
    timer = setInterval(() => (i >= steps.length - 1 ? stop() : go(i + 1)), HOLD_MS);
  }
  play.addEventListener("click", () => (timer ? stop() : start()));
  document.getElementById("next").addEventListener("click", () => { stop(); go(i + 1); });
  document.getElementById("back").addEventListener("click", () => { stop(); go(i - 1); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { stop(); go(i + 1); }
    if (e.key === "ArrowLeft") { stop(); go(i - 1); }
  });
  where.textContent = `Step 1 of ${steps.length}`;
  bar.hidden = false;
})();
"""

PERSON = """<svg aria-hidden="true" width="0" height="0" style="position:absolute">
  <symbol id="person" viewBox="0 0 40 90">
    <circle cx="20" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="4"/>
    <path d="M20 22V56M20 31L6 47M20 31L34 47M20 56L10 86M20 56L30 86" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
  </symbol>
</svg>"""


def render(page):
    """Return the full portable HTML for a PAGE dict."""
    steps_html = []
    for n, st in enumerate(page["steps"], 1):
        paras = "".join(f"<p>{p}</p>" for p in st["p"])
        if st.get("analogy"):
            paras += f'<p class="analogy">Analogy, not from the source: {st["analogy"]}</p>'
        cls = f' {st["cls"]}' if st.get("cls") else ""
        steps_html.append(
            f'<section class="step{cls}" data-step="{n}" id="step-{n}">\n{st["svg"]}\n'
            f'<div class="copy"><span class="num">STEP {n} · {esc(st["label"])}</span>'
            f'<h2>{st["h2"]}</h2>{paras}</div>\n</section>')
    recap = page["recap"]
    foot = "".join(f"<span>{f}</span>" for f in page["footer"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>{esc(page['title'])}</title>
<style>{CSS}</style>
</head>
<body>
{PERSON}
<div class="bar" id="bar" hidden>
  <button type="button" class="primary" id="play">Play</button>
  <button type="button" id="back" aria-label="Previous step">Back</button>
  <button type="button" id="next" aria-label="Next step">Next</button>
  <span class="where" id="where" aria-live="polite">Step 1</span>
  <div class="track" aria-hidden="true"><i id="fill"></i></div>
</div>
<main class="wrap">
<header class="hero">
  <span class="tag">{esc(page['tag'])}</span>
  <h1>{page['h1']}</h1>
  <p>{page['lede']}</p>
  {page['hero']}
</header>
{chr(10).join(steps_html)}
<section class="recap"><span class="tag">Recap</span><h2>{recap['h2']}</h2>{recap['svg']}</section>
<footer>{foot}</footer>
</main>
<script>{JS}</script>
</body>
</html>
"""

# ---------- output location ----------


def work_folder(root, course, week):
    """<root>/<course>/Week-XX_*/Work for the section's week; exactly one match."""
    course_dir = os.path.join(root, course)
    weeks = [d for d in os.listdir(course_dir) if d.startswith(f"Week-{week:02d}_")]
    if len(weeks) != 1:
        raise ValueError(f"expected one Week-{week:02d}_* folder in {course_dir}, found {weeks}")
    return os.path.join(course_dir, weeks[0], "Work")


def add_readme_line(work, fname, blurb):
    readme = os.path.join(work, "README.md")
    # A new README gets a title naming its week folder, like the kit's own Work READMEs.
    body = (open(readme, encoding="utf-8").read() if os.path.exists(readme)
            else f"# {os.path.basename(os.path.dirname(os.path.abspath(work)))} Work\n")
    if fname in body:
        return
    entry = f"- [`{fname}`]({fname}) — {blurb} Review aid only, not graded work.\n"
    heading = "## ELI5 explainers\n"
    if heading not in body:
        body = body.rstrip("\n") + "\n\n" + heading + "\n" + entry
    else:
        # Insert at the end of the ELI5 section, before any later "## " section.
        start = body.index(heading) + len(heading)
        nxt = body.find("\n## ", start)
        end = len(body) if nxt == -1 else nxt + 1
        section = body[start:end].rstrip("\n") + "\n"
        rest = body[end:]
        body = body[:start] + section + entry + ("\n" + rest if rest else "")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write(body)


def load_page(spec_path):
    # Specs may import helpers from sibling specs in the same folder.
    sys.path.insert(0, os.path.dirname(os.path.abspath(spec_path)))
    mod_spec = importlib.util.spec_from_file_location("eli5_spec", spec_path)
    if mod_spec is None or mod_spec.loader is None:
        raise ValueError(f"cannot load spec {spec_path}")
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    return mod.PAGE


def build(page, root=None, out=None):
    """Render, check, and write one page. Returns (path, check summary)."""
    html_text = render(page)
    errors, parsed = eli5.check(html_text)
    if errors:
        raise ValueError("page fails eli5 check:\n  " + "\n  ".join(errors))
    work = None
    if root:
        work = work_folder(root, page["course"], page["week"])
        out = os.path.join(work, f"{page['slug']}-eli5.html")
    if out is None:
        raise ValueError("give root (course topic) or out (any other topic)")
    if os.path.exists(out) and "data-step" not in open(out, encoding="utf-8").read():
        raise ValueError(f"refusing to replace a file that is not an ELI5 page: {out}")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html_text)
    if work:
        add_readme_line(work, os.path.basename(out), page["blurb"])
    return out, f"{len(parsed.steps)} steps, {len(parsed.svgs)} inline SVGs, {parsed.words} visible words"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build an ELI5 page from a spec module.")
    ap.add_argument("spec", nargs="+", help="spec .py files defining PAGE")
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--root", help="term folder holding <course>/Week-XX_*/Work")
    where.add_argument("--out", help="output .html path (single spec only)")
    args = ap.parse_args(argv)
    if args.out and len(args.spec) > 1:
        ap.error("--out takes a single spec")
    status = 0
    for spec in args.spec:
        try:
            LABEL_WARNINGS.clear()
            path, summary = build(load_page(spec), root=args.root, out=args.out)
            print(f"OK {path}: {summary}")
            for warning in LABEL_WARNINGS:
                print(f"WARN {warning}")
        except (ValueError, KeyError, OSError) as exc:
            print(f"FAIL {spec}: {exc}")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
