#!/usr/bin/env python3
"""Safely install the Obsidian study loop into an existing vault directory.

Dry-run by default. ``--apply`` creates missing scaffold files and appends one
small pointer block to agent instruction files. Existing study state, protocol,
manual, notes, and session records are never replaced.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "references" / "study-protocol-template.md"
MANUAL_PATH = SKILL_DIR / "references" / "manpage.md"

PROTOCOL_NAME = "STUDY-PROTOCOL.md"
MANUAL_NAME = "STUDY-MANUAL.md"
MANUAL_BANNER = (
    "<!-- Installed copy of the obsidian-study-loop manual. "
    "Refreshed on protocol sync; do not hand-edit. -->\n"
)
POINTER_SENTENCE = (
    "When I ask to study, quiz, or review notes, follow the workflow in "
    "`STUDY-PROTOCOL.md`."
)
POINTER_BLOCK = f"## Study sessions\n{POINTER_SENTENCE}\n"
POINTER_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")

STUDY_README = """# _study

State and session logs for the Obsidian study loop. Managed by the study
workflow in `STUDY-PROTOCOL.md`. Do not hand-edit `state.json` unless
recovering.

- `sessions/` stores study-session logs and assessment history.
- `visuals/` stores explicit current-scope Markdown and Mermaid review artifacts.
  These are study aids, not quizzes or mastery evidence.
- Automatic chapter-end HTML from `visualize-study-chapter` is helper-owned and
  lives separately in the vault's `Visuals/` folder when that helper is available.
- `dives/` stores teaching-dive notes (`teach-complex-concepts`) — decoupled
  explanations and diagrams, never graded study notes and never mastery
  evidence. Canonical study notes live in `Notes/`, authored only by the
  quiz → assess → write-notes flow.
- `research/` stores session-integrated research-dive workspaces
  (`evidence-research-loop`). Stage files there are source material for gap
  research, never mastery evidence.
- `workpages/` stores note-refresh history archives (one per note). When a
  re-quiz proves mastery, retired note scaffold is filed here verbatim so the
  study note reads clean. These are archives, never mastery evidence; the
  session file stays canonical.
- `quizzes/` is legacy archival space from the deprecated HTML quiz experiment.
  Do not generate, ingest, score, or rely on files there for the active process.
"""


class InstallError(RuntimeError):
    """Expected user-facing installation failure."""


@dataclass(frozen=True)
class Change:
    action: str
    path: Path
    content: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely install the disk-backed Obsidian study loop."
    )
    parser.add_argument(
        "vault_path",
        nargs="?",
        default=".",
        help="Existing Obsidian vault directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--notes-dir",
        type=Path,
        help=(
            "Vault-local notes directory. Defaults to the existing protocol's "
            "NOTES_DIR or Notes on a first install."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the displayed plan. Without this flag, no files are changed.",
    )
    return parser.parse_args(argv)


def resolve_vault(raw: str) -> Path:
    vault = Path(raw).expanduser().resolve()
    if not vault.exists():
        raise InstallError(f"Vault path does not exist: {vault}")
    if not vault.is_dir():
        raise InstallError(f"Vault path is not a directory: {vault}")
    return vault


def resolve_notes_dir(raw: Path, vault: Path) -> Path:
    candidate = raw.expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(vault):
        raise InstallError(f"Notes directory is outside the vault: {resolved}")
    return resolved


def reject_symlink_components(path: Path, vault: Path) -> None:
    try:
        relative = path.relative_to(vault)
    except ValueError as exc:
        raise InstallError(f"Target is outside the vault: {path}") from exc
    current = vault
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            raise InstallError(f"Refusing symlinked vault path component: {current}")


def configured_notes_dir(raw: Path | None, vault: Path) -> Path | None:
    if raw is not None:
        return resolve_notes_dir(raw, vault)
    protocol = vault / PROTOCOL_NAME
    if protocol.exists():
        ensure_safe_path(protocol, vault)
        try:
            text = protocol.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise InstallError(f"Cannot read existing protocol: {protocol}: {exc}") from exc
        match = re.search(r"^- `NOTES_DIR`: `([^`]+)`", text, flags=re.MULTILINE)
        if match:
            return resolve_notes_dir(Path(match.group(1)), vault)
        # Existing custom protocols are preserved even when they predate the
        # parseable NOTES_DIR contract. Do not guess and create a second notes tree.
        return None
    return resolve_notes_dir(Path("Notes"), vault)


def ensure_safe_path(path: Path, vault: Path) -> None:
    reject_symlink_components(path, vault)
    try:
        parent = path.parent.resolve()
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"Cannot resolve target parent safely: {path}: {exc}") from exc
    if not parent.is_relative_to(vault):
        raise InstallError(f"Target escapes the vault: {path}")
    if path.is_symlink():
        raise InstallError(f"Refusing to modify symlinked target: {path}")


def validate_existing_state(path: Path, vault: Path) -> None:
    if not path.exists():
        return
    ensure_safe_path(path, vault)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"Existing study state is invalid: {path}: {exc}") from exc
    if not isinstance(state, dict) or set(state) != {"active_session"}:
        raise InstallError(
            f"Existing study state must contain exactly active_session: {path}"
        )
    active = state["active_session"]
    if active is None:
        return
    if not isinstance(active, str) or not active:
        raise InstallError("Existing active_session must be a non-empty string or null")
    relative = PurePosixPath(active)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[:2] != ("_study", "sessions")
        or relative.suffix != ".md"
    ):
        raise InstallError(
            "Existing active_session must be a vault-relative Markdown path under "
            "_study/sessions/"
        )
    session = vault.joinpath(*relative.parts)
    if not session.exists() or not session.is_file():
        raise InstallError(
            f"Existing active_session must point to a regular file: {active}"
        )
    try:
        resolved_session = session.resolve()
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"Cannot resolve existing active_session safely: {exc}") from exc
    if not resolved_session.is_relative_to(vault / "_study" / "sessions"):
        raise InstallError("Existing active_session resolves outside _study/sessions/")


def render_protocol(vault: Path, notes_dir: Path) -> str:
    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InstallError(f"Cannot read bundled protocol template: {exc}") from exc
    rendered = template.replace("<VAULT_PATH>", str(vault)).replace(
        "<NOTES_DIR>", str(notes_dir)
    )
    if re.search(r"<(?:VAULT_PATH|NOTES_DIR)>", rendered):
        raise InstallError("Bundled protocol contains unresolved path placeholders")
    return rendered if rendered.endswith("\n") else rendered + "\n"


def render_manual() -> str:
    try:
        manual = MANUAL_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InstallError(f"Cannot read bundled manual: {exc}") from exc
    return MANUAL_BANNER + manual.lstrip("\n")


STUDY_SECTION = re.compile(
    r"(?ms)^## Study sessions\s*\n(?P<body>.*?)(?=^##\s|\Z)"
)


def has_pointer(text: str) -> bool:
    section = STUDY_SECTION.search(text)
    return bool(section and "STUDY-PROTOCOL.md" in section.group("body"))


def append_pointer_text(existing: str) -> str:
    if has_pointer(existing):
        return existing
    section = STUDY_SECTION.search(existing)
    if section:
        body = section.group("body").rstrip()
        replacement = (body + "\n" if body else "") + POINTER_SENTENCE + "\n\n"
        tail = existing[section.end("body") :].lstrip("\n")
        return existing[: section.start("body")] + replacement + tail
    prefix = existing.rstrip()
    return (prefix + "\n\n" if prefix else "") + POINTER_BLOCK


def build_plan(vault: Path, notes_dir: Path | None) -> list[Change]:
    state_path = vault / "_study" / "state.json"
    validate_existing_state(state_path, vault)

    changes: list[Change] = []
    directories = tuple(
        directory
        for directory in (
            notes_dir,
            vault / "_study",
            vault / "_study" / "sessions",
            vault / "_study" / "visuals",
            vault / "_study" / "dives",
            vault / "_study" / "research",
            vault / "_study" / "workpages",
        )
        if directory is not None
    )
    for directory in directories:
        ensure_safe_path(directory, vault)
        if directory.exists():
            if not directory.is_dir() or not directory.resolve().is_relative_to(vault):
                raise InstallError(f"Expected a safe vault-local directory: {directory}")
        else:
            changes.append(Change("create directory", directory))

    if not (vault / PROTOCOL_NAME).exists() and notes_dir is None:
        raise InstallError("A notes directory is required for a first install")
    create_files = {
        vault / MANUAL_NAME: render_manual(),
        state_path: '{\n  "active_session": null\n}\n',
        vault / "_study" / "README.md": STUDY_README,
    }
    if not (vault / PROTOCOL_NAME).exists():
        assert notes_dir is not None
        create_files[vault / PROTOCOL_NAME] = render_protocol(vault, notes_dir)
    for target, content in create_files.items():
        ensure_safe_path(target, vault)
        if target.exists() and not target.is_file():
            raise InstallError(f"Expected a regular scaffold file: {target}")
        if not target.exists():
            changes.append(Change("create file", target, content))

    for directory in (
        vault / "_study" / "sessions",
        vault / "_study" / "visuals",
        vault / "_study" / "dives",
        vault / "_study" / "research",
        vault / "_study" / "workpages",
    ):
        keep = directory / ".gitkeep"
        ensure_safe_path(keep, vault)
        if keep.exists() and not keep.is_file():
            raise InstallError(f"Expected a regular scaffold file: {keep}")
        if not keep.exists():
            changes.append(Change("create file", keep, ""))

    for name in POINTER_FILES:
        target = vault / name
        ensure_safe_path(target, vault)
        if not target.exists():
            changes.append(Change("create pointer file", target, POINTER_BLOCK))
            continue
        try:
            existing = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise InstallError(f"Cannot read existing pointer file: {target}: {exc}") from exc
        updated = append_pointer_text(existing)
        if updated != existing:
            changes.append(Change("append pointer block", target, updated))
    return changes


def atomic_write(target: Path, content: str, vault: Path) -> None:
    ensure_safe_path(target, vault)
    previous_mode = target.stat().st_mode & 0o777 if target.exists() else None
    temporary: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if previous_mode is not None:
            temporary.chmod(previous_mode)
        # Re-check immediately before replacement so a newly introduced symlink
        # or redirected parent is rejected rather than followed.
        ensure_safe_path(target, vault)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def apply_plan(changes: list[Change], vault: Path) -> None:
    for change in changes:
        ensure_safe_path(change.path, vault)
        if change.action == "create directory":
            change.path.mkdir(parents=True, exist_ok=False)
        else:
            assert change.content is not None
            atomic_write(change.path, change.content, vault)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        vault = resolve_vault(args.vault_path)
        notes_dir = configured_notes_dir(args.notes_dir, vault)
        changes = build_plan(vault, notes_dir)
        if not changes:
            print(f"ALREADY INSTALLED: {vault}")
            print("Existing state and files were preserved.")
            return 0
        for change in changes:
            print(f"PLAN: {change.action}: {change.path.relative_to(vault)}")
        if not args.apply:
            print("\nDRY RUN: no files changed. Re-run with --apply to install.")
            return 2
        apply_plan(changes, vault)
        print(f"INSTALLED: {vault}")
        print("Existing protocol, manual, state, notes, and sessions were preserved.")
        return 0
    except (InstallError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
