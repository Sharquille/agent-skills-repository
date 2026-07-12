#!/usr/bin/env python3
"""Sync installed Obsidian study-loop protocol and manual documents.

Dry-run by default: prints a unified diff and exits with code 2 when the vault
documents are stale. Use --apply to update both installed copies.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from pathlib import PurePosixPath


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_TEMPLATE = SKILL_DIR / "references" / "study-protocol-template.md"
DEFAULT_MANUAL = SKILL_DIR / "references" / "manpage.md"
PROTOCOL_NAME = "STUDY-PROTOCOL.md"
MANUAL_NAME = "STUDY-MANUAL.md"
MANUAL_BANNER = (
    "<!-- Installed copy of the obsidian-study-loop manual. "
    "Refreshed on protocol sync; do not hand-edit. -->\n"
)


class SyncError(RuntimeError):
    """Expected user-facing sync failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync a vault-local STUDY-PROTOCOL.md from obsidian-study-loop."
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
            "Notes directory to render into the protocol. Relative paths are "
            "resolved from the vault. Defaults to the existing protocol value "
            "or <vault>/Notes."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Refresh installed protocol and manual copies. Without this, only prints diffs.",
    )
    parser.add_argument(
        "--no-diff",
        action="store_true",
        help="Suppress unified diff output.",
    )
    return parser.parse_args()


def resolve_vault(path: str) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.exists():
        raise SyncError(f"Vault path does not exist: {vault}")
    if not vault.is_dir():
        raise SyncError(f"Vault path is not a directory: {vault}")
    protocol = vault / PROTOCOL_NAME
    state = vault / "_study" / "state.json"
    if not protocol.exists() or not state.exists():
        raise SyncError(
            "Refusing to sync an uninstalled or partial study vault. Expected "
            "both STUDY-PROTOCOL.md and _study/state.json; run "
            "install_study_loop.py first to create missing scaffold safely."
        )
    for required in (protocol, state):
        if not required.is_file():
            raise SyncError(f"Required study-vault file is not a regular file: {required}")
        try:
            resolved_required = required.resolve()
        except (OSError, RuntimeError) as exc:
            raise SyncError(f"Required study-vault file is unsafe: {required}: {exc}") from exc
        if not resolved_required.is_relative_to(vault):
            raise SyncError(f"Required study-vault file resolves outside vault: {required}")
    return vault


def read_existing_protocol(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def resolve_notes_dir(path: Path, vault: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = vault / expanded
    return expanded.resolve()


def notes_dir_from_existing(existing: str, vault: Path) -> Path:
    match = re.search(r"^- `NOTES_DIR`: `([^`]+)`", existing, flags=re.MULTILINE)
    if match:
        return resolve_notes_dir(Path(match.group(1)), vault)
    if existing.strip():
        # A protocol exists but its NOTES_DIR line is missing or malformed.
        # Falling back silently could redirect future notes away from the
        # user's real notes directory; require an explicit choice instead.
        raise SyncError(
            "Existing STUDY-PROTOCOL.md has no parseable NOTES_DIR line. "
            "Re-run with --notes-dir <path> to state it explicitly."
        )
    return (vault / "Notes").resolve()


def render_template(template_path: Path, vault: Path, notes_dir: Path) -> str:
    if not template_path.exists():
        raise SyncError(f"Template not found: {template_path}")
    text = template_path.read_text(encoding="utf-8")
    rendered = text.replace("<VAULT_PATH>", str(vault)).replace("<NOTES_DIR>", str(notes_dir))
    unresolved = sorted(set(re.findall(r"<(?:VAULT_PATH|NOTES_DIR)>", rendered)))
    if unresolved:
        raise SyncError(
            "Bundled template still contains unresolved placeholders: "
            + ", ".join(unresolved)
        )
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def ensure_safe_target(target: Path, vault: Path) -> None:
    if target.is_symlink():
        raise SyncError(f"Refusing to replace symlinked protocol target: {target}")
    if target.parent.resolve() != vault:
        raise SyncError(f"Protocol target escaped the vault root: {target}")


def atomic_write_text(target: Path, text: str) -> None:
    previous_mode = target.stat().st_mode & 0o777 if target.exists() else None
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if previous_mode is not None:
            temporary_path.chmod(previous_mode)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def state_warnings(vault: Path) -> list[str]:
    state_file = vault / "_study" / "state.json"
    if not state_file.exists():
        return []
    if state_file.is_symlink():
        try:
            if not state_file.resolve().is_relative_to(vault):
                return [f"{state_file} is a symlink outside the vault"]
        except (OSError, RuntimeError) as exc:
            return [f"{state_file} symlink cannot be resolved safely: {exc}"]
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{state_file} is not valid UTF-8 JSON: {exc}"]
    if not isinstance(state, dict) or set(state) != {"active_session"}:
        return [f"{state_file} must contain exactly the active_session key"]
    active = state["active_session"]
    if active is None:
        return []
    if not isinstance(active, str) or not active:
        return [f"{state_file} active_session must be a non-empty string or null"]
    relative = PurePosixPath(active)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[:2] != ("_study", "sessions")
        or relative.suffix != ".md"
    ):
        return [
            f"{state_file} active_session must be a vault-relative Markdown path "
            "under _study/sessions/"
        ]
    session = vault.joinpath(*relative.parts)
    if not session.exists() or not session.is_file():
        return [f"{state_file} active_session must point to a regular file: {active}"]
    sessions_dir = vault / "_study" / "sessions"
    try:
        resolved_session = session.resolve()
    except (OSError, RuntimeError) as exc:
        return [f"{state_file} active_session cannot be resolved safely: {exc}"]
    if not resolved_session.is_relative_to(sessions_dir):
        return [f"{state_file} active_session resolves outside _study/sessions/"]
    return []


def print_state_warnings(vault: Path) -> None:
    for warning in state_warnings(vault):
        print(f"WARNING: {warning}", file=sys.stderr)


def unified_diff(current: str, desired: str, target: Path, template: Path) -> str:
    return "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            desired.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(template),
        )
    )


def rendered_manual() -> str:
    if not DEFAULT_MANUAL.exists():
        raise SyncError(f"Manual source not found: {DEFAULT_MANUAL}")
    text = DEFAULT_MANUAL.read_text(encoding="utf-8")
    return MANUAL_BANNER + text.lstrip("\n")


def main() -> int:
    args = parse_args()
    try:
        vault = resolve_vault(args.vault_path)
        template = DEFAULT_TEMPLATE.resolve()
        target = vault / PROTOCOL_NAME
        manual_source = DEFAULT_MANUAL.resolve()
        manual_target = vault / MANUAL_NAME
        ensure_safe_target(target, vault)
        ensure_safe_target(manual_target, vault)
        state_issues = state_warnings(vault)
        if state_issues:
            raise SyncError(
                "Refusing to sync while study state needs repair: "
                + "; ".join(state_issues)
            )
        current = read_existing_protocol(target)
        current_manual = read_existing_protocol(manual_target)
        notes_dir = (
            resolve_notes_dir(args.notes_dir, vault)
            if args.notes_dir
            else notes_dir_from_existing(current, vault)
        )
        if not notes_dir.is_relative_to(vault):
            raise SyncError(
                f"Notes dir {notes_dir} is outside the vault {vault}. "
                "The protocol permits only vault-local note directories."
            )
        desired = render_template(template, vault, notes_dir)
        desired_manual = rendered_manual()

        protocol_stale = current != desired
        manual_stale = current_manual != desired_manual
        if not protocol_stale and not manual_stale:
            print(f"{target} is already in sync with {template}")
            print(f"{manual_target} is already in sync with {manual_source}")
            return 0

        if not args.no_diff:
            if protocol_stale:
                print(unified_diff(current, desired, target, template), end="")
            if manual_stale:
                print(
                    unified_diff(
                        current_manual, desired_manual, manual_target, manual_source
                    ),
                    end="",
                )

        if not args.apply:
            print(
                "\nDRY RUN: installed study documents are stale. "
                "Re-run with --apply to update them."
            )
            return 2

        if protocol_stale:
            atomic_write_text(target, desired)
            print(f"UPDATED: {target}")
            print(f"SOURCE:  {template}")
        if manual_stale:
            atomic_write_text(manual_target, desired_manual)
            print(f"UPDATED: {manual_target}")
            print(f"SOURCE:  {manual_source}")
        print(
            "Protected: Notes/, _study/sessions/, _study/state.json, and pointer "
            "files were not touched."
        )
        state_file = vault / "_study" / "state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state["active_session"]:
            print(
                "NOTICE: _study/state.json points at an active session. Agents "
                "mid-session should re-read STUDY-PROTOCOL.md before their next "
                "study-loop action."
            )
        return 0
    except (SyncError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
