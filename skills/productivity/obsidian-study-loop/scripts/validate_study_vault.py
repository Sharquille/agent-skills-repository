#!/usr/bin/env python3
"""Read-only integrity checks for an Obsidian study-loop vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


PROTOCOL_NAME = "STUDY-PROTOCOL.md"
SESSION_STATUSES = {"studying", "quizzed", "notes-written", "reviewed"}
HEADING_PATTERN = re.compile(r"^## (.+)$", flags=re.MULTILINE)
STUDY_CHECK_START = re.compile(
    r"<!-- study-check:start\s+id=([^\s>]+)[^>]*-->", flags=re.MULTILINE
)
STUDY_CHECK_END = re.compile(
    r"<!-- study-check:end\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
LEARNER_EDIT_START = re.compile(
    r"<!-- learner-edit:start\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
LEARNER_EDIT_END = re.compile(
    r"<!-- learner-edit:end\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
VISUAL_LABEL = "Visual review artifact - not an assessment"
FORBIDDEN_VISUAL_ELEMENTS = {
    "base",
    "embed",
    "form",
    "iframe",
    "input",
    "object",
    "select",
    "textarea",
}
URL_ATTRIBUTES = {"action", "cite", "formaction", "href", "poster", "src", "srcset"}
FORBIDDEN_SCRIPT_PATTERNS = {
    "network API": re.compile(
        r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon)\b",
        flags=re.IGNORECASE,
    ),
    "persistent storage API": re.compile(
        r"\b(?:localStorage|sessionStorage|indexedDB|caches|document\.cookie)\b",
        flags=re.IGNORECASE,
    ),
    "device or clipboard API": re.compile(
        r"\b(?:geolocation|mediaDevices|clipboard\.write)\b",
        flags=re.IGNORECASE,
    ),
    "dynamic code execution": re.compile(
        r"\b(?:eval\s*\(|new\s+Function\s*\(|Function\s*\()",
        flags=re.IGNORECASE,
    ),
    "dynamic import": re.compile(r"\bimport\s*\(", flags=re.IGNORECASE),
}


class ValidationError(RuntimeError):
    """Expected user-facing validation failure."""


@dataclass(frozen=True)
class Issue:
    severity: str
    path: Path
    message: str


class VisualArtifactParser(HTMLParser):
    """Collect the small static surface needed for visual-artifact validation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.visible_text: list[str] = []
        self.script_text: list[str] = []
        self.style_text: list[str] = []
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self._script_depth = 0
        self._style_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        normalized_tag = tag.lower()
        normalized_attrs = {name.lower(): value for name, value in attrs}
        self.elements.append((normalized_tag, normalized_attrs))
        element_id = normalized_attrs.get("id")
        if element_id:
            self.ids.add(element_id)
        href = normalized_attrs.get("href")
        if href and href.startswith("#") and len(href) > 1:
            self.fragments.append(href[1:])
        if normalized_tag == "script":
            self._script_depth += 1
        elif normalized_tag == "style":
            self._style_depth += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() == "script":
            self._script_depth -= 1
        elif tag.lower() == "style":
            self._style_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag == "script" and self._script_depth:
            self._script_depth -= 1
        elif normalized_tag == "style" and self._style_depth:
            self._style_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._script_depth:
            self.script_text.append(data)
        elif self._style_depth:
            self.style_text.append(data)
        elif data.strip():
            self.visible_text.append(data.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an Obsidian study-loop vault without modifying it."
    )
    parser.add_argument(
        "vault_path",
        nargs="?",
        default=".",
        help="Obsidian vault path. Defaults to the current directory.",
    )
    parser.add_argument(
        "--notes-dir",
        type=Path,
        help=(
            "Override the notes directory. Relative paths are resolved from the "
            "vault and must stay inside it."
        ),
    )
    return parser.parse_args()


def resolve_vault(path: str) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.is_dir():
        raise ValidationError(f"Vault path is not a directory: {vault}")
    markers = [
        vault / PROTOCOL_NAME,
        vault / "_study" / "state.json",
        vault / ".obsidian",
    ]
    if not any(marker.exists() for marker in markers):
        raise ValidationError(
            "Target does not look like a study vault. Expected STUDY-PROTOCOL.md, "
            "_study/state.json, or .obsidian/."
        )
    return vault


def resolve_inside_vault(path: Path, vault: Path, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = vault / expanded
    resolved = expanded.resolve()
    if not resolved.is_relative_to(vault):
        raise ValidationError(f"{label} is outside the vault: {resolved}")
    return resolved


def display_path(path: Path, vault: Path) -> Path:
    try:
        return path.relative_to(vault)
    except ValueError:
        return path


def read_utf8(path: Path, issues: list[Issue]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(Issue("ERROR", path, f"cannot read UTF-8 text: {exc}"))
        return None


def frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end]


def frontmatter_value(block: str | None, key: str) -> str | None:
    if block is None:
        return None
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", block, flags=re.MULTILINE)
    return match.group(1) if match else None


def heading_group(title: str) -> int | None:
    if title == "Study content":
        return 1
    if title == "Unit progress":
        return 2
    if title.startswith("Quiz progress — "):
        return 3
    if title.startswith("Assessment — "):
        return 4
    if title.startswith("Notes written — "):
        return 5
    if title.startswith("Review — "):
        return 6
    if title == "Mastery evidence":
        return 7
    if title == "Session log":
        return 8
    return None


def heading_blocks(text: str) -> list[tuple[str, int, int]]:
    matches = list(HEADING_PATTERN.finditer(text))
    return [
        (
            match.group(1).strip(),
            match.start(),
            matches[index + 1].start() if index + 1 < len(matches) else len(text),
        )
        for index, match in enumerate(matches)
    ]


def validate_session(path: Path, vault: Path, issues: list[Issue]) -> None:
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault / "_study" / "sessions"):
                issues.append(Issue("ERROR", path, "session symlink resolves outside the vault"))
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"session symlink is unsafe: {exc}"))
            return
    text = read_utf8(path, issues)
    if text is None:
        return
    block = frontmatter(text)
    if block is None:
        issues.append(Issue("ERROR", path, "missing or unterminated frontmatter"))
    else:
        for key in ("topic", "created", "status", "objectives"):
            if not re.search(rf"^{key}:\s*", block, flags=re.MULTILINE):
                issues.append(Issue("ERROR", path, f"frontmatter is missing {key}"))
        status = frontmatter_value(block, "status")
        if status is not None and status not in SESSION_STATUSES:
            issues.append(Issue("ERROR", path, f"unsupported session status: {status}"))

    headings = heading_blocks(text)
    titles = [title for title, _, _ in headings]
    for title, count in Counter(titles).items():
        if count > 1:
            issues.append(Issue("ERROR", path, f"duplicate H2 heading: {title}"))

    if titles.count("Session log") != 1:
        issues.append(Issue("ERROR", path, "must contain exactly one ## Session log"))
    elif titles[-1] != "Session log":
        issues.append(Issue("ERROR", path, "## Session log must be the final H2"))

    previous_group = 0
    for title in titles:
        group = heading_group(title)
        if group is None:
            issues.append(Issue("WARN", path, f"unrecognized session H2: {title}"))
            continue
        if group < previous_group:
            issues.append(
                Issue("ERROR", path, f"heading is outside canonical group order: {title}")
            )
        previous_group = max(previous_group, group)

    for title, start, end in headings:
        section = text[start:end]
        if title.startswith("Quiz progress — ") and "Consumed by Assessment —" not in section:
            issues.append(Issue("WARN", path, f"unconsumed {title}"))

    for logged in re.findall(r"Wrote `([^`]+\.md)`", text):
        relative = PurePosixPath(logged)
        if relative.is_absolute() or ".." in relative.parts:
            issues.append(Issue("ERROR", path, f"unsafe logged note path: {logged}"))
            continue
        note_path = vault.joinpath(*relative.parts)
        if not note_path.exists():
            issues.append(Issue("ERROR", path, f"logged note does not exist: {logged}"))
        else:
            try:
                resolved_note = note_path.resolve()
            except (OSError, RuntimeError) as exc:
                issues.append(Issue("ERROR", path, f"logged note path is unsafe: {exc}"))
                continue
            if not resolved_note.is_relative_to(vault):
                issues.append(
                    Issue("ERROR", path, f"logged note resolves outside vault: {logged}")
                )


def marker_counts(
    path: Path,
    starts: re.Pattern[str],
    ends: re.Pattern[str],
    text: str,
    label: str,
    issues: list[Issue],
) -> None:
    start_counts = Counter(starts.findall(text))
    end_counts = Counter(ends.findall(text))
    for marker_id in sorted(set(start_counts) | set(end_counts)):
        if start_counts[marker_id] != 1 or end_counts[marker_id] != 1:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{label} {marker_id} must have exactly one start and one end marker",
                )
            )
            continue
        matching_start = next(
            match for match in starts.finditer(text) if match.group(1) == marker_id
        )
        matching_end = next(match for match in ends.finditer(text) if match.group(1) == marker_id)
        if matching_end.start() < matching_start.end():
            issues.append(Issue("ERROR", path, f"{label} {marker_id} ends before it starts"))


def study_check_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for start in STUDY_CHECK_START.finditer(text):
        marker_id = start.group(1)
        closing = next(
            (
                match
                for match in STUDY_CHECK_END.finditer(text, start.end())
                if match.group(1) == marker_id
            ),
            None,
        )
        if closing is not None:
            blocks.append((marker_id, text[start.start() : closing.end()]))
    return blocks


def check_is_answered(block: str) -> bool:
    if re.search(r"^- \[[xX]\] ", block, flags=re.MULTILINE):
        return True
    answer_lines = re.findall(
        r"<!-- learner-answer:[^>]+ -->\s*\n([^\n]+)", block, flags=re.MULTILINE
    )
    return any("Write here." not in line for line in answer_lines)


def validate_note(
    path: Path,
    vault: Path,
    issues: list[Issue],
    check_locations: dict[str, list[Path]],
) -> None:
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault):
                issues.append(Issue("ERROR", path, "note symlink resolves outside the vault"))
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"note symlink is unsafe: {exc}"))
            return
    text = read_utf8(path, issues)
    if text is None:
        return
    block = frontmatter(text)
    status = frontmatter_value(block, "status")
    marker_counts(path, STUDY_CHECK_START, STUDY_CHECK_END, text, "study-check", issues)
    marker_counts(path, LEARNER_EDIT_START, LEARNER_EDIT_END, text, "learner-edit", issues)

    for marker_id, check_block in study_check_blocks(text):
        check_locations[marker_id].append(path)
        answered = check_is_answered(check_block)
        reviewed = "**Review —" in check_block
        if answered and not reviewed:
            severity = "ERROR" if status == "reviewed" else "WARN"
            issues.append(
                Issue(severity, path, f"answered study-check has no review: {marker_id}")
            )

    pending_gap = re.search(
        r"<!-- learner-edit:start\s+id=gap-[^>]+-->.*?\bWrite here\.\s*"
        r"<!-- learner-edit:end\s+id=gap-[^>]+-->",
        text,
        flags=re.DOTALL,
    )
    if status == "reviewed" and pending_gap:
        issues.append(Issue("ERROR", path, "reviewed note still contains a pending gap"))
    if status == "reviewed" and "RESEARCH NEEDED" in text:
        issues.append(Issue("ERROR", path, "reviewed note still says RESEARCH NEEDED"))


def visual_meta(
    elements: list[tuple[str, dict[str, str | None]]], name: str
) -> str | None:
    for tag, attrs in elements:
        if tag != "meta":
            continue
        if (attrs.get("name") or "").lower() == name.lower():
            return attrs.get("content")
    return None


def visual_csp(
    elements: list[tuple[str, dict[str, str | None]]]
) -> str | None:
    for tag, attrs in elements:
        if tag != "meta":
            continue
        if (attrs.get("http-equiv") or "").lower() == "content-security-policy":
            return attrs.get("content")
    return None


def allowed_local_url(value: str) -> bool:
    stripped = value.strip()
    return (
        not stripped
        or stripped == "#"
        or stripped.startswith("#")
        or stripped.lower().startswith("data:image/")
    )


def validate_visual_artifact(path: Path, vault: Path, issues: list[Issue]) -> None:
    visuals_root = vault / "_study" / "visuals"
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(visuals_root):
                issues.append(
                    Issue("ERROR", path, "visual artifact symlink resolves outside _study/visuals")
                )
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"visual artifact symlink is unsafe: {exc}"))
            return

    text = read_utf8(path, issues)
    if text is None:
        return
    parser = VisualArtifactParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # HTMLParser surfaces malformed entities as ValueError.
        issues.append(Issue("ERROR", path, f"cannot parse HTML: {exc}"))
        return

    elements = parser.elements
    visible_text = " ".join(parser.visible_text)
    tags = [tag for tag, _ in elements]
    if VISUAL_LABEL not in visible_text:
        issues.append(Issue("ERROR", path, f"missing visible label: {VISUAL_LABEL}"))

    html_attrs = next((attrs for tag, attrs in elements if tag == "html"), {})
    if not html_attrs.get("lang"):
        issues.append(Issue("ERROR", path, "html element is missing lang"))
    if "main" not in tags:
        issues.append(Issue("ERROR", path, "missing main landmark"))
    if tags.count("h1") != 1:
        issues.append(Issue("ERROR", path, "must contain exactly one h1"))

    charset_present = any(
        tag == "meta" and bool(attrs.get("charset")) for tag, attrs in elements
    )
    if not charset_present:
        issues.append(Issue("ERROR", path, "missing meta charset"))
    if not visual_meta(elements, "viewport"):
        issues.append(Issue("ERROR", path, "missing viewport metadata"))
    if (visual_meta(elements, "referrer") or "").lower() != "no-referrer":
        issues.append(Issue("ERROR", path, "referrer policy must be no-referrer"))
    for field in ("study-source", "study-scope", "study-generated", "study-visual-version"):
        if not visual_meta(elements, field):
            issues.append(Issue("ERROR", path, f"missing {field} metadata"))

    csp = visual_csp(elements)
    required_csp = (
        "default-src 'none'",
        "connect-src 'none'",
        "form-action 'none'",
        "base-uri 'none'",
    )
    if csp is None:
        issues.append(Issue("ERROR", path, "missing Content-Security-Policy metadata"))
    else:
        csp_normalized = " ".join(csp.split()).lower()
        for directive in required_csp:
            if directive not in csp_normalized:
                issues.append(Issue("ERROR", path, f"CSP is missing {directive}"))
        if "*" in csp:
            issues.append(Issue("ERROR", path, "CSP must not contain a wildcard source"))

    for tag, attrs in elements:
        if tag in FORBIDDEN_VISUAL_ELEMENTS:
            issues.append(Issue("ERROR", path, f"forbidden element: {tag}"))
        if tag == "script" and attrs.get("src"):
            issues.append(Issue("ERROR", path, "external script source is forbidden"))
        if tag == "script" and (attrs.get("type") or "").lower() == "module":
            issues.append(Issue("ERROR", path, "module scripts are not file-URL portable"))
        for name, value in attrs.items():
            if name.startswith("on"):
                issues.append(Issue("ERROR", path, f"inline event handler is forbidden: {name}"))
            if name in URL_ATTRIBUTES and value is not None:
                values = value.split(",") if name == "srcset" else [value]
                if any(not allowed_local_url(item.strip().split()[0]) for item in values if item.strip()):
                    issues.append(Issue("ERROR", path, f"non-local {name} reference: {value}"))
        if tag == "svg":
            has_name = bool(attrs.get("aria-label") or attrs.get("aria-labelledby"))
            decorative = (attrs.get("aria-hidden") or "").lower() == "true"
            if not has_name and not decorative:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        "svg must have an accessible name or aria-hidden=true",
                    )
                )

    for fragment in parser.fragments:
        if fragment not in parser.ids:
            issues.append(Issue("ERROR", path, f"fragment target does not exist: #{fragment}"))

    scripts = "\n".join(parser.script_text)
    for label, pattern in FORBIDDEN_SCRIPT_PATTERNS.items():
        if pattern.search(scripts):
            issues.append(Issue("ERROR", path, f"forbidden {label} in inline script"))

    styles = "\n".join(parser.style_text)
    if re.search(r"@import\b", styles, flags=re.IGNORECASE):
        issues.append(Issue("ERROR", path, "CSS @import is forbidden"))
    for match in re.finditer(r"url\(([^)]+)\)", styles, flags=re.IGNORECASE):
        target = match.group(1).strip(" \t\r\n\"'")
        if not allowed_local_url(target):
            issues.append(Issue("ERROR", path, f"non-local CSS url reference: {target}"))
    if ("animation" in styles or "transition" in styles) and not re.search(
        r"prefers-reduced-motion\s*:\s*reduce", styles, flags=re.IGNORECASE
    ):
        issues.append(Issue("ERROR", path, "motion is present without a reduced-motion override"))
    if any(tag in {"a", "button", "details", "summary"} for tag in tags) and ":focus-visible" not in styles:
        issues.append(Issue("ERROR", path, "interactive content lacks a focus-visible style"))


def validate_state(vault: Path, issues: list[Issue]) -> None:
    path = vault / "_study" / "state.json"
    if not path.exists():
        issues.append(Issue("ERROR", path, "missing study state file"))
        return
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault):
                issues.append(
                    Issue("ERROR", path, "state file symlink resolves outside the vault")
                )
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"state file symlink is unsafe: {exc}"))
            return
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        issues.append(Issue("ERROR", path, f"invalid UTF-8 JSON: {exc}"))
        return
    if not isinstance(state, dict) or set(state) != {"active_session"}:
        issues.append(Issue("ERROR", path, "must contain exactly the active_session key"))
        return
    active = state["active_session"]
    if active is None:
        return
    if not isinstance(active, str) or not active:
        issues.append(Issue("ERROR", path, "active_session must be a string or null"))
        return
    relative = PurePosixPath(active)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[:2] != ("_study", "sessions")
        or relative.suffix != ".md"
    ):
        issues.append(
            Issue(
                "ERROR",
                path,
                "active_session must be a vault-relative Markdown path under _study/sessions/",
            )
        )
        return
    session = vault.joinpath(*relative.parts)
    if not session.exists():
        issues.append(Issue("ERROR", path, f"active session does not exist: {active}"))
    else:
        try:
            resolved_session = session.resolve()
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"active session is unsafe: {exc}"))
            return
        if not resolved_session.is_relative_to(vault / "_study" / "sessions"):
            issues.append(Issue("ERROR", path, "active session resolves outside _study/sessions/"))


def notes_dir_from_protocol(vault: Path, override: Path | None) -> Path:
    if override is not None:
        return resolve_inside_vault(override, vault, "Notes directory")
    protocol = vault / PROTOCOL_NAME
    if protocol.exists():
        if protocol.is_symlink():
            try:
                if not protocol.resolve().is_relative_to(vault):
                    raise ValidationError("STUDY-PROTOCOL.md is a symlink outside the vault")
            except (OSError, RuntimeError) as exc:
                raise ValidationError(f"STUDY-PROTOCOL.md symlink is unsafe: {exc}") from exc
        text = protocol.read_text(encoding="utf-8")
        match = re.search(r"^- `NOTES_DIR`: `([^`]+)`", text, flags=re.MULTILINE)
        if match:
            return resolve_inside_vault(Path(match.group(1)), vault, "NOTES_DIR")
    return (vault / "Notes").resolve()


def validate_vault(vault: Path, notes_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    validate_state(vault, issues)

    sessions_dir = vault / "_study" / "sessions"
    if not sessions_dir.is_dir():
        issues.append(Issue("ERROR", sessions_dir, "missing sessions directory"))
    else:
        for session in sorted(sessions_dir.glob("*.md")):
            validate_session(session, vault, issues)

    check_locations: dict[str, list[Path]] = defaultdict(list)
    if not notes_dir.is_dir():
        issues.append(Issue("WARN", notes_dir, "notes directory does not exist"))
    else:
        for note in sorted(notes_dir.rglob("*.md")):
            validate_note(note, vault, issues, check_locations)
    for marker_id, paths in sorted(check_locations.items()):
        unique = sorted(set(paths))
        if len(unique) > 1:
            locations = ", ".join(str(display_path(path, vault)) for path in unique)
            issues.append(
                Issue("ERROR", vault, f"duplicate study-check id {marker_id}: {locations}")
            )

    visuals_dir = vault / "_study" / "visuals"
    if visuals_dir.exists() and not visuals_dir.is_dir():
        issues.append(Issue("ERROR", visuals_dir, "visuals path is not a directory"))
    elif visuals_dir.is_dir():
        for artifact in sorted(visuals_dir.glob("*.html")):
            validate_visual_artifact(artifact, vault, issues)
    return issues


def main() -> int:
    args = parse_args()
    try:
        vault = resolve_vault(args.vault_path)
        notes_dir = notes_dir_from_protocol(vault, args.notes_dir)
        issues = validate_vault(vault, notes_dir)
    except (ValidationError, OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for issue in issues:
        print(f"{issue.severity}: {display_path(issue.path, vault)}: {issue.message}")
    errors = sum(issue.severity == "ERROR" for issue in issues)
    warnings = sum(issue.severity == "WARN" for issue in issues)
    if errors:
        print(f"FAILED: {errors} error(s), {warnings} warning(s).")
        return 1
    print(f"OK: no integrity errors; {warnings} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
