#!/usr/bin/env python3
"""Assemble tactile study-surface v2 artifacts from shared chrome + scope content.

Usage: assemble.py <content-module.py> <output.html>
Each content module defines META (dict) and SECTIONS (list) and CUES (list).
"""
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
CSS = (HERE / "chrome.css").read_text()
JS = (HERE / "behaviors.js").read_text()

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <meta name="study-source" content="{source}">
  <meta name="study-scope" content="{scope}">
  <meta name="study-generated" content="{generated}">
  <meta name="study-visual-version" content="1">
  <title>{title}</title>
  <style>
{css}
    :root {{ --accent: {accent}; }}
  </style>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="cmd">
    <span class="brand">Sec+ field unit</span>
    <span class="scope-code">{code}</span>
    <span class="cmd-title">{scope_name}</span>
    <span class="cmd-spacer"></span>
    <span class="keys" aria-hidden="true">
      <span class="hint"><span class="kbd">j</span><span class="kbd">k</span> cues</span>
      <span class="hint"><span class="kbd">o</span> open</span>
      <span class="hint"><span class="kbd">g</span> got it</span>
      <span class="hint"><span class="kbd">a</span> again</span>
    </span>
    <button type="button" class="btn" data-theme-toggle>theme</button>
  </header>
  <div class="frame">
    <nav class="rail" aria-label="Sections">
      <span class="rail-label">Index</span>
{rail_links}
    </nav>
    <main id="main">
      <section class="thesis" id="top">
        <p class="posture">Visual review artifact - not an assessment</p>
        <p class="kicker">{kicker}</p>
        <h1>{h1}</h1>
        <p class="lede">{lede}</p>
      </section>
{sections}
      <section class="panel" id="retrieval" data-sec>
        <div class="sec-head"><span class="sec-no">{cue_no}</span><h2>Retrieval deck</h2></div>
        <p class="sec-lede">Say your answer aloud before opening a reference. Marks are for this sitting only — nothing is collected, scored, or stored, and everything resets on reload.</p>
        <div class="deck-bar">
          <span class="tally" data-tally>{cue_count} cues</span>
          <button type="button" class="btn" data-reveal-all>reveal all</button>
          <button type="button" class="btn" data-hide-all>hide all</button>
          <button type="button" class="btn" data-reset-marks>reset marks</button>
        </div>
{cues}
      </section>
    </main>
  </div>
  <footer class="trace">
    <div><strong>Source</strong>{source}</div>
    <div><strong>Scope</strong>{scope}</div>
    <div><strong>Generated</strong>{generated}</div>
    <div><strong>Contract</strong>study visual v1 · surface v2 (TS7-built)</div>
    <div class="boundary">Visual review only - not an assessment. Mastery evidence stays in the chat study loop.</div>
  </footer>
  <script>
{js}
  </script>
</body>
</html>
"""

SECTION = """      <section class="panel" id="{sid}" data-sec>
        <div class="sec-head"><span class="sec-no">{no}</span><h2>{title}</h2></div>
        <p class="sec-lede">{lede}</p>
{body}
      </section>
"""

CUE = """        <article class="cue" data-cue data-mark="unmarked">
          <details>
            <summary>{q}<span class="cue-state" aria-hidden="true"></span></summary>
            <p>{a}</p>
          </details>
          <div class="cue-actions">
            <button type="button" class="btn" data-mark-got>got it</button>
            <button type="button" class="btn" data-mark-again>again</button>
          </div>
        </article>
"""


def main() -> None:
    mod_path, out_path = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location("content", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    meta, sections, cues = mod.META, mod.SECTIONS, mod.CUES

    rail = []
    body = []
    for i, sec in enumerate(sections, start=1):
        no = f"{i:02d}"
        rail.append(
            f'      <a href="#{sec["id"]}"><span class="no">{no}</span>{sec["nav"]}</a>'
        )
        body.append(
            SECTION.format(sid=sec["id"], no=no, title=sec["title"], lede=sec["lede"], body=sec["body"])
        )
    cue_no = f"{len(sections) + 1:02d}"
    rail.append(
        f'      <a href="#retrieval"><span class="no">{cue_no}</span>Retrieval deck</a>'
    )

    html = PAGE.format(
        css=CSS,
        js=JS,
        rail_links="\n".join(rail),
        sections="".join(body),
        cues="".join(CUE.format(q=q, a=a) for q, a in cues),
        cue_no=cue_no,
        cue_count=len(cues),
        **meta,
    )
    pathlib.Path(out_path).write_text(html)
    print(f"wrote {out_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
