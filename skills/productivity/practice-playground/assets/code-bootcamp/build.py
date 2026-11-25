#!/usr/bin/env python3
"""Inline styles, content, reference and engine into the shell: dist/m-lab.html (the artifact source)."""
from pathlib import Path
H = Path(__file__).resolve().parent
page = (H / "shell.html").read_text()
mods = "\n".join((H / "modules" / f).read_text() for f in sorted(p.name for p in (H / "modules").glob("mod*.js")))
for tag, text in (("/*STYLES*/", (H / "styles.css").read_text()), ("/*CONTENT*/", (H / "content.js").read_text() + "\n" + mods), ("/*REF*/", (H / "ref.js").read_text()), ("/*ENGINE*/", (H / "engine.js").read_text())):
    page = page.replace(tag, text)
(H / "dist").mkdir(exist_ok=True)
(H / "dist" / "m-lab.html").write_text(page)
print(f"dist/m-lab.html: {len(page):,} bytes")
