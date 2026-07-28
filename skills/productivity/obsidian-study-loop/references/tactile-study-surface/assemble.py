#!/usr/bin/env python3
"""Legacy HTML compatibility assembler; no longer the active visual system.

New visual review artifacts use Markdown and Mermaid. This module remains only
to support existing HTML artifacts and compatibility tests.

Usage: assemble.py --vault <vault> <content-manifest.json> <output.html>

The manifest is data, never executable code.  Metadata and ordinary text are
escaped.  The one rich-text field (``body_html``) is parsed and rebuilt from a
small allowlist of the surface's documented primitives.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import os
import pathlib
import re
import sys
import tempfile
from typing import Any, Sequence


HERE = pathlib.Path(__file__).parent
CSS = (HERE / "chrome.css").read_text(encoding="utf-8")
JS = (HERE / "behaviors.js").read_text(encoding="utf-8")

META_KEYS = {
    "source",
    "scope",
    "code",
    "scope_name",
    "generated",
    "title",
    "accent",
    "kicker",
    "h1",
    "lede",
}
SECTION_KEYS = {"id", "nav", "title", "lede", "body_html"}
CUE_KEYS = {"question", "reference"}
RESERVED_IDS = {"main", "top", "retrieval"}
SAFE_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
URI_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
LOCAL_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}\Z")
SAFE_ACCENT = re.compile(
    r"oklch\("
    r"(?P<lightness>(?:0(?:\.\d+)?|1(?:\.0+)?))\s+"
    r"(?P<chroma>(?:0(?:\.\d+)?|0?\.\d+))\s+"
    r"(?P<hue>(?:\d+(?:\.\d+)?))"
    r"\)\Z"
)
URL_ATTRS = {"action", "cite", "formaction", "href", "poster", "src", "srcset"}
VOID_TAGS: set[str] = set()

# The component vocabulary documented in SPEC.md.  Classes are scoped to the
# elements on which the bundled stylesheet defines them.
ALLOWED_TAGS = {
    "article",
    "code",
    "div",
    "em",
    "h3",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
ALLOWED_CLASSES = {
    "article": {"card", "span-all"},
    "div": {
        "a",
        "b",
        "chips",
        "cols-3",
        "cols-5",
        "cols-6",
        "contrast",
        "duo",
        "flow",
        "grid-2",
        "grid-3",
        "grid-4",
        "span-all",
        "table-wrap",
        "vs",
    },
    "span": {"chip", "tag", "vs-mark", "warn"},
}

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src {script_policy}; img-src data:; font-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
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
    <span class="brand">Study review</span>
    <span class="scope-code">{code}</span>
    <span class="cmd-title">{scope_name}</span>
    <span class="cmd-spacer"></span>
{header_controls}
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
{retrieval_section}
    </main>
  </div>
  <footer class="trace">
    <div><strong>Source</strong>{source}</div>
    <div><strong>Scope</strong>{scope}</div>
    <div><strong>Generated</strong>{generated}</div>
    <div><strong>Contract</strong>study visual v1 · tactile surface v2</div>
    <div class="boundary">Visual review artifact - not an assessment. Mastery evidence stays in the chat study loop.</div>
  </footer>
{script_block}
</body>
</html>
"""

INTERACTIVE_HEADER = """    <span class="keys" aria-hidden="true">
      <span class="hint"><span class="kbd">j</span><span class="kbd">k</span> cues</span>
      <span class="hint"><span class="kbd">o</span> open</span>
      <span class="hint"><span class="kbd">g</span> got it</span>
      <span class="hint"><span class="kbd">a</span> again</span>
    </span>
    <button type="button" class="btn" data-theme-toggle>theme</button>"""

RETRIEVAL = """      <section class="panel" id="retrieval" data-sec>
        <div class="sec-head"><span class="sec-no">{cue_no}</span><h2>Retrieval deck</h2></div>
        <p class="sec-lede">Say your answer aloud before opening a reference. Marks are for this sitting only — nothing is collected, scored, or stored, and everything resets on reload.</p>
        <div class="deck-bar">
          <span class="tally" data-tally>{cue_count} cues</span>
          <button type="button" class="btn" data-reveal-all>reveal all</button>
          <button type="button" class="btn" data-hide-all>hide all</button>
          <button type="button" class="btn" data-reset-marks>reset marks</button>
        </div>
{cues}
      </section>"""

SECTION = """      <section class="panel" id="{sid}" data-sec>
        <div class="sec-head"><span class="sec-no">{no}</span><h2>{title}</h2></div>
        <p class="sec-lede">{lede}</p>
{body}
      </section>
"""

CUE = """        <article class="cue" data-cue data-mark="unmarked">
          <details>
            <summary>{question}<span class="cue-state" aria-hidden="true"></span></summary>
            <p>{reference}</p>
          </details>
          <div class="cue-actions">
            <button type="button" class="btn" data-mark-got>got it</button>
            <button type="button" class="btn" data-mark-again>again</button>
          </div>
        </article>
"""


class ManifestError(ValueError):
    """A manifest violates the declarative content contract."""


def _plain_text(value: Any, field: str, *, limit: int = 10_000) -> str:
    if not isinstance(value, str):
        raise ManifestError(f"{field} must be a string")
    if not value.strip():
        raise ManifestError(f"{field} must not be empty")
    if len(value) > limit:
        raise ManifestError(f"{field} exceeds {limit} characters")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ManifestError(f"{field} contains a control character")
    return value


def _exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        parts = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if unknown:
            parts.append("unknown " + ", ".join(unknown))
        raise ManifestError(f"{field} has invalid fields: {'; '.join(parts)}")
    return value


def _validate_source(source: str) -> None:
    if "\\" in source or "://" in source or URI_SCHEME.match(source):
        raise ManifestError("meta.source must be a vault-local POSIX path")
    path = pathlib.PurePosixPath(source)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ManifestError("meta.source must be a vault-local POSIX path")


def _validate_generated(generated: str) -> None:
    if not LOCAL_TIMESTAMP.fullmatch(generated):
        raise ManifestError(
            "meta.generated must be a local ISO datetime with numeric offset"
        )
    try:
        parsed = dt.datetime.strptime(generated, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError as exc:
        raise ManifestError(
            "meta.generated must be a local ISO datetime with numeric offset"
        ) from exc
    if parsed.utcoffset() is None:
        raise ManifestError("meta.generated must include a numeric UTC offset")


def _validate_accent(accent: str) -> None:
    match = SAFE_ACCENT.fullmatch(accent)
    if not match:
        raise ManifestError("meta.accent must be a single numeric oklch(L C H) color")
    chroma = float(match.group("chroma"))
    hue = float(match.group("hue"))
    if chroma > 0.5 or hue > 360:
        raise ManifestError("meta.accent oklch chroma or hue is outside the safe range")


class _PrimitiveSanitizer(HTMLParser):
    """Validate and rebuild one body fragment from known surface primitives."""

    def __init__(self, field: str) -> None:
        super().__init__(convert_charrefs=True)
        self.field = field
        self.output: list[str] = []
        self.stack: list[str] = []

    def _fail(self, message: str) -> None:
        raise ManifestError(f"{self.field}: {message}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            self._fail(f"element <{tag}> is not allowed")
        seen: set[str] = set()
        rendered_attrs: list[str] = []
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            if name in seen:
                self._fail(f"duplicate attribute {name!r} on <{tag}>")
            seen.add(name)
            if name.startswith("on"):
                self._fail(f"event-handler attribute {name!r} is not allowed")
            if name in URL_ATTRS:
                self._fail(f"URL-bearing attribute {name!r} is not allowed")
            if name == "id":
                self._fail("body ids are not allowed; use the section id")
            if name != "class":
                self._fail(f"attribute {name!r} is not allowed on <{tag}>")
            if raw_value is None:
                self._fail("class must have a value")
            classes = raw_value.split()
            if not classes or len(classes) != len(set(classes)):
                self._fail("class must contain unique class names")
            allowed = ALLOWED_CLASSES.get(tag, set())
            unknown = sorted(set(classes) - allowed)
            if unknown:
                self._fail(f"unknown class on <{tag}>: {', '.join(unknown)}")
            grids = {"grid-2", "grid-3", "grid-4"}.intersection(classes)
            columns = {"cols-3", "cols-5", "cols-6"}.intersection(classes)
            if len(grids) > 1 or len(columns) > 1:
                self._fail("conflicting layout classes are not allowed")
            if columns and "flow" not in classes:
                self._fail("cols-* classes require the flow primitive")
            if "warn" in classes and "tag" not in classes:
                self._fail("warn is only valid with the tag primitive")
            rendered_attrs.append(
                f' class="{html.escape(" ".join(classes), quote=True)}"'
            )
        self.output.append(f"<{tag}{''.join(rendered_attrs)}>")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            self._fail(f"closing element </{tag}> is not allowed")
        if not self.stack or self.stack[-1] != tag:
            expected = self.stack[-1] if self.stack else "no element"
            self._fail(f"mismatched </{tag}>; expected closing tag for {expected}")
        self.stack.pop()
        self.output.append(f"</{tag}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._fail(f"self-closing element <{tag}/> is not allowed")

    def handle_data(self, data: str) -> None:
        self.output.append(html.escape(data, quote=False))

    def handle_comment(self, data: str) -> None:
        self._fail("comments are not allowed")

    def handle_decl(self, decl: str) -> None:
        self._fail("declarations are not allowed")

    def handle_pi(self, data: str) -> None:
        self._fail("processing instructions are not allowed")

    def unknown_decl(self, data: str) -> None:
        self._fail("unknown declarations are not allowed")

    def finish(self) -> str:
        self.close()
        if self.stack:
            self._fail(f"unclosed element <{self.stack[-1]}>")
        return "".join(self.output)


def sanitize_body(fragment: Any, field: str) -> str:
    source = _plain_text(fragment, field, limit=500_000)
    sanitizer = _PrimitiveSanitizer(field)
    try:
        sanitizer.feed(source)
        return sanitizer.finish()
    except ManifestError:
        raise
    except Exception as exc:  # HTMLParser errors become a concise CLI message.
        raise ManifestError(f"{field}: invalid HTML fragment: {exc}") from exc


def validate_manifest(value: Any) -> dict[str, Any]:
    root = _exact_keys(value, {"meta", "sections", "cues"}, "manifest")
    meta = _exact_keys(root["meta"], META_KEYS, "meta")
    clean_meta = {
        key: _plain_text(meta[key], f"meta.{key}", limit=2_000) for key in META_KEYS
    }
    _validate_source(clean_meta["source"])
    _validate_generated(clean_meta["generated"])
    _validate_accent(clean_meta["accent"])

    raw_sections = root["sections"]
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ManifestError("sections must be a non-empty array")
    if len(raw_sections) > 64:
        raise ManifestError("sections must contain at most 64 entries")
    sections = []
    seen_ids = set(RESERVED_IDS)
    for index, raw_section in enumerate(raw_sections):
        field = f"sections[{index}]"
        section = _exact_keys(raw_section, SECTION_KEYS, field)
        sid = _plain_text(section["id"], f"{field}.id", limit=64)
        if not SAFE_ID.fullmatch(sid):
            raise ManifestError(
                f"{field}.id must be a lowercase, hyphen-separated safe HTML id"
            )
        if sid in seen_ids:
            raise ManifestError(f"{field}.id duplicates or reserves id {sid!r}")
        seen_ids.add(sid)
        sections.append(
            {
                "id": sid,
                "nav": _plain_text(section["nav"], f"{field}.nav", limit=200),
                "title": _plain_text(section["title"], f"{field}.title", limit=500),
                "lede": _plain_text(section["lede"], f"{field}.lede", limit=4_000),
                "body_html": sanitize_body(section["body_html"], f"{field}.body_html"),
            }
        )

    raw_cues = root["cues"]
    if not isinstance(raw_cues, list):
        raise ManifestError("cues must be an array")
    if len(raw_cues) > 200:
        raise ManifestError("cues must contain at most 200 entries")
    cues = []
    for index, raw_cue in enumerate(raw_cues):
        field = f"cues[{index}]"
        cue = _exact_keys(raw_cue, CUE_KEYS, field)
        cues.append(
            {
                "question": _plain_text(cue["question"], f"{field}.question", limit=4_000),
                "reference": _plain_text(cue["reference"], f"{field}.reference", limit=8_000),
            }
        )
    return {"meta": clean_meta, "sections": sections, "cues": cues}


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    if path.suffix.lower() != ".json":
        raise ManifestError("content manifest must use the .json extension")
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {path}: {exc}") from exc

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ManifestError(f"manifest contains duplicate JSON key {key!r}")
            result[key] = item
        return result

    def reject_nonfinite_constant(value: str) -> None:
        raise ManifestError(f"manifest contains non-JSON numeric constant {value}")

    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_constant,
        )
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return validate_manifest(value)


def render_artifact(manifest: dict[str, Any]) -> str:
    meta = manifest["meta"]
    escaped_meta = {
        key: html.escape(value, quote=True) if key != "accent" else value
        for key, value in meta.items()
    }
    rail = []
    sections = []
    for index, section in enumerate(manifest["sections"], start=1):
        number = f"{index:02d}"
        rail.append(
            f'      <a href="#{section["id"]}"><span class="no">{number}</span>'
            f'{html.escape(section["nav"], quote=False)}</a>'
        )
        sections.append(
            SECTION.format(
                sid=section["id"],
                no=number,
                title=html.escape(section["title"], quote=False),
                lede=html.escape(section["lede"], quote=False),
                body=section["body_html"],
            )
        )
    retrieval_section = ""
    header_controls = ""
    script_block = ""
    script_policy = "'none'"
    if manifest["cues"]:
        cue_no = f"{len(sections) + 1:02d}"
        rail.append(
            f'      <a href="#retrieval"><span class="no">{cue_no}</span>Retrieval deck</a>'
        )
        cues = "".join(
            CUE.format(
                question=html.escape(cue["question"], quote=False),
                reference=html.escape(cue["reference"], quote=False),
            )
            for cue in manifest["cues"]
        )
        retrieval_section = RETRIEVAL.format(
            cue_no=cue_no,
            cue_count=len(manifest["cues"]),
            cues=cues,
        )
        header_controls = INTERACTIVE_HEADER
        script_block = f"  <script>\n{JS}\n  </script>"
        script_policy = "'unsafe-inline'"
    return PAGE.format(
        css=CSS,
        script_policy=script_policy,
        header_controls=header_controls,
        rail_links="\n".join(rail),
        sections="".join(sections),
        retrieval_section=retrieval_section,
        script_block=script_block,
        **escaped_meta,
    )


def validate_vault_paths(
    vault: pathlib.Path, output: pathlib.Path, source: str
) -> None:
    """Confine both output and traceability source to the selected vault."""
    if not vault.is_dir():
        raise ManifestError(f"vault directory does not exist: {vault}")
    try:
        vault_root = vault.resolve(strict=True)
        visuals_root = (vault_root / "_study" / "visuals").resolve(strict=True)
        output_parent = output.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ManifestError(f"cannot resolve vault or visual output safely: {exc}") from exc
    if not visuals_root.is_dir() or not visuals_root.is_relative_to(vault_root):
        raise ManifestError("vault _study/visuals must be a directory inside the vault")
    if output_parent != visuals_root:
        raise ManifestError("output must be directly inside the vault's _study/visuals directory")
    if output.is_symlink():
        raise ManifestError(f"refusing to replace symlinked output: {output}")
    if output.exists() and not output.is_file():
        raise ManifestError(f"output exists but is not a regular file: {output}")

    source_path = vault_root.joinpath(*pathlib.PurePosixPath(source).parts)
    try:
        resolved_source = source_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ManifestError(f"meta.source does not resolve to a vault file: {source}") from exc
    if not resolved_source.is_relative_to(vault_root) or not resolved_source.is_file():
        raise ManifestError("meta.source must resolve to a regular file inside the vault")


def write_atomic(path: pathlib.Path, content: str) -> None:
    if path.is_symlink():
        raise ManifestError(f"refusing to replace symlinked output: {path}")
    parent = path.parent
    if not parent.is_dir():
        raise ManifestError(f"output directory does not exist: {parent}")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_name = handle.name
        pathlib.Path(temp_name).replace(path)
    except OSError as exc:
        raise ManifestError(f"cannot write output {path}: {exc}") from exc
    finally:
        if temp_name:
            temp_path = pathlib.Path(temp_name)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    # The requested output has already failed. Avoid replacing
                    # that concise error with a cleanup traceback.
                    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble a self-contained tactile study artifact from safe JSON data."
    )
    parser.add_argument(
        "--vault",
        required=True,
        type=pathlib.Path,
        help="vault containing the source note and _study/visuals output directory",
    )
    parser.add_argument("manifest", type=pathlib.Path, help="declarative .json content manifest")
    parser.add_argument("output", type=pathlib.Path, help="output .html file")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.output.suffix.lower() != ".html":
        print("assemble.py: error: output must use the .html extension", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest(args.manifest)
        validate_vault_paths(args.vault, args.output, manifest["meta"]["source"])
        artifact = render_artifact(manifest)
        write_atomic(args.output, artifact)
    except ManifestError as exc:
        print(f"assemble.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(artifact)} bytes)")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
