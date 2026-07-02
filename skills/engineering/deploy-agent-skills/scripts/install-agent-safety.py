#!/usr/bin/env python3
"""Install reproducible local-agent safety guardrails.

The script is intentionally conservative:
- It never deletes user data.
- It backs up files before changing them.
- It merges OpenCode config and appends/replaces managed Markdown blocks.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path


BEGIN = "<!-- agent-skills-repository:safety:begin -->"
END = "<!-- agent-skills-repository:safety:end -->"


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments from JSONC while preserving string values."""
    output: list[str] = []
    i = 0
    in_string = False
    escape = False
    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            i += 1
            continue

        if char == "/" and next_char == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        if char == "/" and next_char == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue

        output.append(char)
        i += 1

    return "".join(output)


def load_jsonc(path: Path) -> OrderedDict:
    if not path.exists():
        return OrderedDict()
    text = path.read_text()
    if not text.strip():
        return OrderedDict()
    return json.loads(strip_jsonc(text), object_pairs_hook=OrderedDict)


def render_template(text: str, repo_dir: Path, home: Path) -> str:
    agents_skills = home / ".agents" / "skills"
    return (
        text.replace("{{REPO_DIR}}", str(repo_dir))
        .replace("{{HOME}}", str(home))
        .replace("{{AGENTS_SKILLS}}", str(agents_skills))
    )


def backup(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.name}.backup.{stamp}")
    if dry_run:
        print(f"  would back up {path} -> {backup_path}")
        return
    shutil.copy2(path, backup_path)
    print(f"  backed up {path} -> {backup_path}")


def ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def merge_rule_object(existing: object, safety: object) -> object:
    if not isinstance(existing, dict) or not isinstance(safety, dict):
        return safety

    result: OrderedDict[str, object] = OrderedDict()

    # Put non-deny safety defaults first, then preserve custom rules, then place
    # safety denies last because OpenCode uses the last matching rule.
    for key, value in safety.items():
        if value != "deny":
            result[key] = value

    for key, value in existing.items():
        if key not in safety:
            result[key] = value

    for key, value in safety.items():
        if value == "deny":
            result[key] = value

    return result


def merge_opencode(existing: OrderedDict, safety: OrderedDict) -> OrderedDict:
    merged = OrderedDict(existing)
    merged.setdefault("$schema", "https://opencode.ai/config.json")

    existing_skills = merged.get("skills", OrderedDict())
    if not isinstance(existing_skills, dict):
        existing_skills = OrderedDict()
    safety_skills = safety.get("skills", OrderedDict())
    existing_paths = list(existing_skills.get("paths", [])) if isinstance(existing_skills.get("paths", []), list) else []
    safety_paths = list(safety_skills.get("paths", [])) if isinstance(safety_skills.get("paths", []), list) else []
    existing_skills["paths"] = ordered_unique(existing_paths + safety_paths)
    merged["skills"] = existing_skills

    existing_permissions = merged.get("permission", OrderedDict())
    if not isinstance(existing_permissions, dict):
        existing_permissions = OrderedDict()
    safety_permissions = safety.get("permission", OrderedDict())
    for permission_name, safety_value in safety_permissions.items():
        existing_permissions[permission_name] = merge_rule_object(
            existing_permissions.get(permission_name),
            safety_value,
        )
    merged["permission"] = existing_permissions

    return merged


def write_if_changed(path: Path, content: str, dry_run: bool) -> bool:
    current = path.read_text() if path.exists() else None
    if current == content:
        print(f"  unchanged: {path}")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path, dry_run)
    if dry_run:
        print(f"  would write {path}")
        return True
    path.write_text(content)
    print(f"  wrote {path}")
    return True


def looks_like_legacy_generated_safety(text: str) -> bool:
    stripped = text.strip()
    first_line = stripped.splitlines()[0] if stripped else ""
    lower = stripped.lower()
    return (
        first_line.startswith("# Global ")
        and first_line.endswith(" Safety Rules")
        and "~/.claude" in lower
        and "uninstall" in lower
    )


def merge_managed_block(existing: str, block: str) -> str:
    managed = f"{BEGIN}\n{block.rstrip()}\n{END}\n"
    if BEGIN in existing and END in existing:
        before = existing.split(BEGIN, 1)[0].rstrip()
        after = existing.split(END, 1)[1].lstrip()
        if looks_like_legacy_generated_safety(before):
            before = ""
        pieces = [piece for piece in (before, managed.rstrip(), after.rstrip()) if piece]
        return "\n\n".join(pieces) + "\n"

    if looks_like_legacy_generated_safety(existing):
        return managed

    if existing.strip():
        return existing.rstrip() + "\n\n" + managed
    return managed


def install_markdown_template(template: Path, dest: Path, repo_dir: Path, home: Path, dry_run: bool) -> None:
    block = render_template(template.read_text(), repo_dir, home)
    existing = dest.read_text() if dest.exists() else ""
    content = merge_managed_block(existing, block)
    write_if_changed(dest, content, dry_run)


def install_opencode_config(asset_dir: Path, repo_dir: Path, home: Path, dry_run: bool) -> None:
    dest = home / ".config" / "opencode" / "opencode.jsonc"
    template = asset_dir / "opencode-safety.json"
    safety = json.loads(
        render_template(template.read_text(), repo_dir, home),
        object_pairs_hook=OrderedDict,
    )
    existing = load_jsonc(dest)
    merged = merge_opencode(existing, safety)
    content = json.dumps(merged, indent=2) + "\n"
    write_if_changed(dest, content, dry_run)


def install_safety(repo_dir: Path, home: Path, dry_run: bool, targets: set[str]) -> None:
    asset_dir = repo_dir / "skills" / "engineering" / "deploy-agent-skills" / "assets" / "safety"
    if not asset_dir.exists():
        raise SystemExit(f"safety assets not found: {asset_dir}")

    def wants(target: str) -> bool:
        return "all" in targets or target in targets

    print("--- Installing local agent safety guardrails ---")
    if wants("opencode-config"):
        install_opencode_config(asset_dir, repo_dir, home, dry_run)
    if wants("opencode-agents"):
        install_markdown_template(asset_dir / "opencode-AGENTS.md", home / ".config" / "opencode" / "AGENTS.md", repo_dir, home, dry_run)
    if wants("claude"):
        install_markdown_template(asset_dir / "claude-CLAUDE.md", home / ".claude" / "CLAUDE.md", repo_dir, home, dry_run)
    if wants("gemini"):
        install_markdown_template(asset_dir / "gemini-GEMINI.md", home / ".gemini" / "GEMINI.md", repo_dir, home, dry_run)
    if wants("codex"):
        install_markdown_template(asset_dir / "codex-AGENTS.md", home / ".codex" / "AGENTS.md", repo_dir, home, dry_run)
    print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install local agent safety guardrails from this repository.")
    parser.add_argument("--repo-dir", type=Path, required=True)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--target",
        action="append",
        choices=["all", "opencode-config", "opencode-agents", "claude", "gemini", "codex"],
        help="Install only one target. Repeat for multiple targets. Defaults to all.",
    )
    args = parser.parse_args()

    targets = set(args.target or ["all"])
    install_safety(args.repo_dir.expanduser().resolve(), args.home.expanduser().resolve(), args.dry_run, targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
