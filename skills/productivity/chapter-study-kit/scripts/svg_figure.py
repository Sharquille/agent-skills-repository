#!/usr/bin/env python3
"""Primitives for Core figures: palette colours, labels, boxes, circles, arrows.

Import this from a scratch script, compose one figure per idea, and write it
beside the section notes as an .svg. validate_kit.py checks the result (palette,
accessibility, no scripts or links, numbers that the notes or ledger supply).
Stdlib only; no network.
"""
from __future__ import annotations

from pathlib import Path

# Same meaning, same colour, in every figure (references/visual-language.md).
GREEN = dict(fill="#E7F4EC", stroke="#6FA98A", ink="#2F4F3C")        # population, parameter, descriptive
NAVY = dict(fill="#EEF3F8", stroke="#1F3A5F", ink="#1F3A5F")         # sample, statistic
PURPLE = dict(fill="#EFE9FA", stroke="#9B8AB8", ink="#3E3357")       # variable hub, individuals
PURPLE_LEAF = dict(fill="#F8F4FD", stroke="#B9A9D1", ink="#4A3D63")  # variable leaves
PEACH = dict(fill="#FBEFE3", stroke="#C98F5A", ink="#5C4023")        # inferential, traps, errors
WHITE = dict(fill="#FFFFFF", stroke="#C9D3DD", ink="#1F2933")
INK, MUTED, ARROW = "#1F2933", "#5B6B7A", "#1F3A5F"


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def text(x: float, y: float, s: str, size: float = 12, ink: str = INK, anchor: str = "middle",
         weight: str = "normal", italic: bool = False) -> str:
    style = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{ink}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{style}>{esc(s)}</text>')


def lines(x: float, y: float, rows: list[str], size: float = 12, ink: str = INK, anchor: str = "middle",
          weight: str = "normal", gap: float | None = None) -> str:
    gap = gap or size + 3
    return "".join(text(x, y + i * gap, row, size, ink, anchor, weight) for i, row in enumerate(rows))


def box(x: float, y: float, w: float, h: float, c: dict, rx: float = 6, dash: bool = False, sw: float = 1.4) -> str:
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{c["fill"]}" '
            f'stroke="{c["stroke"]}" stroke-width="{sw}"{d}/>')


def circle(cx: float, cy: float, r: float, c: dict, dash: bool = False, sw: float = 1.6) -> str:
    d = ' stroke-dasharray="6 4"' if dash else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="{sw}"{d}/>'


def arrow(x1: float, y1: float, x2: float, y2: float, ink: str = ARROW, dash: bool = False, sw: float = 1.5) -> str:
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ink}" stroke-width="{sw}"{d} '
            f'marker-end="url(#ah)"/>')


def figure(w: float, h: float, body: str, label: str) -> str:
    """A whole SVG document; label is what a screen reader says and must describe the idea."""
    if not label.strip():
        raise ValueError("a figure needs a label that states its idea")
    defs = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ARROW}"/></marker></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{esc(label)}">{defs}{body}</svg>\n')


def write(path: Path, svg: str) -> Path:
    path = Path(path)
    if path.suffix != ".svg":
        raise ValueError("figures are .svg files beside the section notes")
    path.write_text(svg)
    return path
