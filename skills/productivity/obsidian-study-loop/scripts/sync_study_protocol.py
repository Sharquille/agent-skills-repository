#!/usr/bin/env python3
"""Sync an Obsidian study vault protocol from the bundled template.

Dry-run by default: prints a unified diff and exits with code 2 when the vault
protocol is stale. Use --apply to update STUDY-PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_TEMPLATE = SKILL_DIR / "references" / "study-protocol-template.md"
PROTOCOL_NAME = "STUDY-PROTOCOL.md"


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
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help="Template path. Defaults to the bundled study-protocol-template.md.",
    )
    parser.add_argument(
        "--notes-dir",
        type=Path,
        help="Notes directory to render into the protocol. Defaults to the existing protocol value or <vault>/Notes.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the rendered protocol to STUDY-PROTOCOL.md. Without this, only prints a diff.",
    )
    parser.add_argument(
        "--allow-external-notes-dir",
        action="store_true",
        help="Permit a --notes-dir outside the vault. Off by default because the protocol promises vault-local writes.",
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
    markers = [vault / PROTOCOL_NAME, vault / "_study" / "state.json", vault / ".obsidian"]
    if not any(marker.exists() for marker in markers):
        raise SyncError(
            "Refusing to sync: target does not look like a study vault. "
            "Expected STUDY-PROTOCOL.md, _study/state.json, or .obsidian/."
        )
    return vault


def read_existing_protocol(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def notes_dir_from_existing(existing: str, vault: Path) -> Path:
    match = re.search(r"^- `NOTES_DIR`: `([^`]+)`", existing, flags=re.MULTILINE)
    if match:
        return Path(match.group(1)).expanduser().resolve()
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
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def unified_diff(current: str, desired: str, target: Path, template: Path) -> str:
    return "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            desired.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(template),
        )
    )


def main() -> int:
    args = parse_args()
    try:
        vault = resolve_vault(args.vault_path)
        template = args.template.expanduser().resolve()
        target = vault / PROTOCOL_NAME
        current = read_existing_protocol(target)
        notes_dir = args.notes_dir.expanduser().resolve() if args.notes_dir else notes_dir_from_existing(current, vault)
        if not args.allow_external_notes_dir and not notes_dir.is_relative_to(vault):
            raise SyncError(
                f"Notes dir {notes_dir} is outside the vault {vault}. "
                "The protocol promises vault-local writes; pass "
                "--allow-external-notes-dir to override deliberately."
            )
        desired = render_template(template, vault, notes_dir)

        if current == desired:
            print(f"{target} is already in sync with {template}")
            return 0

        if not args.no_diff:
            print(unified_diff(current, desired, target, template), end="")

        if not args.apply:
            print("\nDRY RUN: protocol is stale. Re-run with --apply to update STUDY-PROTOCOL.md.")
            return 2

        target.write_text(desired, encoding="utf-8")
        print(f"UPDATED: {target}")
        print(f"SOURCE:  {template}")
        print("Protected: Notes/, _study/sessions/, and _study/state.json were not touched.")
        state_file = vault / "_study" / "state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                state = {}
            if isinstance(state, dict) and state.get("active_session"):
                print(
                    "NOTICE: _study/state.json points at an active session. Agents mid-session "
                    "should re-read STUDY-PROTOCOL.md before their next study-loop action."
                )
        return 0
    except SyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
