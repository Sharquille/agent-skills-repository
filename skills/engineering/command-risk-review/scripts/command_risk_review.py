#!/usr/bin/env python3
"""Target-aware command risk reviewer.

This helper does not execute commands. It parses a command string and emits a
short risk synopsis for destructive operations and sensitive targets.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


RISK_ORDER = ["low", "medium", "high", "critical"]
CONTROL = {"&&", "||", ";", "|"}


@dataclass
class TargetFinding:
    target: str
    normalized: str
    risk: str
    label: str
    at_stake: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    safer: list[str] = field(default_factory=list)


@dataclass
class OperationFinding:
    operation: str
    risk: str
    targets: list[str]
    notes: list[str] = field(default_factory=list)


def max_risk(*levels: str) -> str:
    return max(levels, key=lambda level: RISK_ORDER.index(level))


def tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def command_segments(tokens: list[str]) -> Iterable[list[str]]:
    segment: list[str] = []
    for token in tokens:
        if token in CONTROL:
            if segment:
                yield segment
                segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def command_name(token: str) -> str:
    return Path(token).name


def normalize_target(target: str) -> str:
    home = str(Path.home())
    value = target.strip()
    value = value.replace("${HOME}", home).replace("$HOME", home)
    if value.startswith("~"):
        value = os.path.expanduser(value)
    return value


def has_any(value: str, needles: Iterable[str]) -> bool:
    lower = value.lower()
    return any(needle.lower() in lower for needle in needles)


def classify_target(target: str) -> TargetFinding:
    normalized = normalize_target(target)
    combined = f"{target} {normalized}"

    finding = TargetFinding(
        target=target,
        normalized=normalized,
        risk="medium",
        label="Filesystem or resource target",
        at_stake=["Files, directories, or resource state selected by the command."],
        scenarios=["The target may contain user data or generated state unless inspected first."],
        safer=["List and size the target before changing it."],
    )

    def set_finding(risk: str, label: str, at_stake: list[str], scenarios: list[str], safer: list[str]) -> TargetFinding:
        finding.risk = risk
        finding.label = label
        finding.at_stake = at_stake
        finding.scenarios = scenarios
        finding.safer = safer
        return finding

    if target in {"/", "/*", ".", "./", "~", "~/", "$HOME", "$HOME/*", "${HOME}", "${HOME}/*"}:
        return set_finding(
            "critical",
            "Broad root/current/home target",
            ["Large mixed data boundary, often including projects, config, app state, and personal files."],
            ["A broad delete can remove unrelated work and recovery metadata in one run."],
            ["Narrow the command to a specific inspected subdirectory, or make a backup first."],
        )

    if any(pattern in target for pattern in (".*", ".[!.]*", "..?*")):
        return set_finding(
            "critical",
            "Hidden-file bulk glob",
            ["Dotfiles and dotdirs such as .git, .claude, .codex, .gemini, .ssh, app configs, and local state."],
            ["A hidden bulk delete can remove agent history, credentials, repository metadata, and settings while looking like cleanup."],
            ["Replace the glob with explicit inspected paths; never approve broad dotfile cleanup by default."],
        )

    if has_any(combined, ["/.claude", " .claude", "~/.claude"]):
        return set_finding(
            "critical",
            "Claude Code user data",
            ["Skills, project JSONL transcripts, settings, MCP/session state, cleanup markers, and recovery metadata."],
            ["Claude can lose prior project conversations; Desktop summaries may point to missing transcripts; repo-backed skills may disappear."],
            ["Uninstall the CLI separately, then inspect or back up ~/.claude before any data cleanup."],
        )

    if has_any(combined, ["/.config/claude", " .config/claude", "~/.config/claude"]):
        return set_finding(
            "high",
            "Claude configuration data",
            ["Claude settings, tool configuration, and user-level agent preferences."],
            ["Deleting config can silently reset behavior and remove safety or integration settings."],
            ["Uninstall the CLI separately; inspect and back up config before removing it."],
        )

    if has_any(combined, ["/.local/share/claude", " .local/share/claude", "~/.local/share/claude"]):
        return set_finding(
            "high",
            "Claude local share data",
            ["Claude local application/tool data, sessions, indexes, or support files depending on install."],
            ["Deleting local share data can remove state that is not recreated by uninstalling a package."],
            ["Inspect and back up before changing; do not bundle with package uninstall."],
        )

    if has_any(combined, ["library/application support/claude"]):
        return set_finding(
            "critical",
            "Claude Desktop application support data",
            ["Desktop local-agent sessions, summaries, app databases, plugin/bundled state, and local cache/state."],
            ["Deleting it can break Desktop history and bundled local-agent behavior, not just uninstall a terminal tool."],
            ["Inspect with du/find first and back up before changing it."],
        )

    if has_any(combined, ["/.agents", " .agents", "~/.agents"]):
        return set_finding(
            "high",
            "Shared agent skills",
            ["OpenCode and shared agent skill symlinks, including repo-backed safety skills."],
            ["OpenCode may stop seeing custom skills after the directory is removed."],
            ["Rebuild links from agent-skills-repository; avoid deleting the directory during cleanup."],
        )

    if has_any(combined, ["/.codex", " .codex", "~/.codex"]):
        return set_finding(
            "critical",
            "Codex user state",
            ["Codex skills, instructions, plugin cache, config, and local thread/tool state."],
            ["Deleting it can remove available skills and break local Codex behavior."],
            ["Inspect and back up before changing; do not mix with unrelated CLI uninstalls."],
        )

    if has_any(combined, ["/.gemini", " .gemini", "~/.gemini"]):
        return set_finding(
            "high",
            "Gemini CLI user state",
            ["Gemini skills, config, and local agent state."],
            ["Deleting it can remove skill discovery and custom Gemini configuration."],
            ["Inspect and back up before changing."],
        )

    if has_any(combined, ["agent-skills-repository"]):
        return set_finding(
            "critical",
            "Agent skills source repository",
            ["The source of truth for custom skills, deployment scripts, safety rules, and reproducibility."],
            ["Deleting it can remove the ability to reinstall safety rules and skills on another machine."],
            ["Commit/push changes and back up before any destructive maintenance."],
        )

    if has_any(combined, ["/.git", " .git"]):
        return set_finding(
            "critical",
            "Git repository internals",
            ["Repository history, refs, hooks, worktrees, and recovery metadata."],
            ["Deleting .git turns a repository into unversioned files and can destroy local-only work history."],
            ["Use git status, git clean dry-runs, and backups instead of deleting .git."],
        )

    if has_any(combined, ["obsidian", "icloud", "mobile documents", "notes"]):
        return set_finding(
            "critical",
            "Knowledge store or sync path",
            ["Notes, study history, attachments, plugins, and synced files that may propagate deletion."],
            ["A local delete can sync to other devices or remove study/vault history."],
            ["Inventory and back up before changing; avoid broad globs in sync folders."],
        )

    if has_any(combined, ["node_modules", ".next", "/dist", "/build", "coverage"]):
        return set_finding(
            "low",
            "Usually rebuildable project output",
            ["Generated dependencies or build artifacts, usually recoverable from lockfiles/source."],
            ["Local patches or generated-only artifacts can still be lost."],
            ["Verify lockfiles/source exist and prefer project-scoped cleanup."],
        )

    if has_any(combined, [".cache", "/caches", "cache"]):
        return set_finding(
            "medium",
            "Cache data",
            ["Usually rebuildable caches, but sometimes downloaded models, indexes, session material, or offline work."],
            ["Cleanup can cost time/network or remove useful local indexes."],
            ["Inspect size and contents first; avoid pairing cache cleanup with config deletion."],
        )

    if target.startswith("http://") or target.startswith("https://"):
        return set_finding(
            "high",
            "Remote API endpoint",
            ["Remote resource state controlled by the endpoint and HTTP method."],
            ["DELETE/POST/PATCH calls can remove or mutate data outside local recovery boundaries."],
            ["Read API docs and confirm environment, tenant, auth scope, and idempotency before calling."],
        )

    return finding


def rm_targets(segment: list[str], start: int) -> tuple[list[str], list[str]]:
    targets: list[str] = []
    flags: list[str] = []
    stop_options = False
    for token in segment[start + 1 :]:
        if token == "--":
            stop_options = True
            continue
        if not stop_options and token.startswith("-") and token != "-":
            flags.append(token)
            continue
        targets.append(token)
    return targets, flags


def analyze_segment(segment: list[str]) -> list[OperationFinding]:
    if not segment:
        return []

    findings: list[OperationFinding] = []

    for index, token in enumerate(segment):
        name = command_name(token)

        if name in {"rm", "unlink", "rmdir", "trash", "shred"}:
            targets, flags = rm_targets(segment, index)
            recursive = any("r" in flag.lower() or "R" in flag for flag in flags)
            force = any("f" in flag.lower() for flag in flags)
            op = name
            if name == "rm" and recursive and force:
                op = "forced recursive delete"
            elif name == "rm" and recursive:
                op = "recursive delete"
            elif name == "rm":
                op = "delete"
            risk = "high" if name in {"rm", "trash", "shred"} else "medium"
            if recursive and force:
                risk = "critical"
            findings.append(OperationFinding(op, risk, targets or ["<missing target>"], [f"flags: {' '.join(flags) or '<none>'}"]))

        if name == "find":
            uses_delete = "-delete" in segment
            uses_exec_rm = "-exec" in segment and any(command_name(t) == "rm" for t in segment)
            if uses_delete or uses_exec_rm:
                target = "."
                for item in segment[index + 1 :]:
                    if item.startswith("-") or item in {"(", ")", "!"}:
                        break
                    target = item
                    break
                label = "find delete" if uses_delete else "find exec rm"
                findings.append(OperationFinding(label, "high", [target], ["find can traverse many files below the target."]))

        if name == "git" and index + 1 < len(segment):
            sub = segment[index + 1]
            if sub == "reset" and "--hard" in segment:
                findings.append(OperationFinding("git reset --hard", "high", ["current repository"], ["Discards working-tree and index changes."]))
            if sub == "clean" and any(flag.startswith("-") and "f" in flag for flag in segment[index + 2 :]):
                findings.append(OperationFinding("git clean", "high", ["current repository"], ["Can delete untracked files; -x also removes ignored files."]))

        if name == "npm" and index + 1 < len(segment) and segment[index + 1] in {"uninstall", "remove", "rm"}:
            packages = [t for t in segment[index + 2 :] if not t.startswith("-")]
            findings.append(OperationFinding("npm package uninstall", "medium", packages or ["<package not specified>"], ["Uninstalls package binaries, but should not imply user-data deletion."]))

        if name == "curl":
            lowered = [t.lower() for t in segment]
            delete = "-x" in lowered and "delete" in lowered
            delete = delete or "--request" in lowered and "delete" in lowered
            if delete:
                urls = [t for t in segment if t.startswith("http://") or t.startswith("https://")]
                findings.append(OperationFinding("HTTP DELETE request", "high", urls or ["<endpoint not detected>"], ["Remote destructive action; local backups may not help."]))

        if name == "aws" and index + 2 < len(segment) and segment[index + 1] == "s3" and segment[index + 2] in {"rm", "rb"}:
            targets = [t for t in segment[index + 3 :] if not t.startswith("-")]
            risk = "critical" if "--recursive" in segment or segment[index + 2] == "rb" else "high"
            findings.append(OperationFinding("AWS S3 delete", risk, targets or ["<s3 target not specified>"], ["Cloud object deletion can be difficult to recover."]))

    return findings


def analyze(command: str) -> dict:
    tokens = tokenize(command)
    operations: list[OperationFinding] = []
    for segment in command_segments(tokens):
        operations.extend(analyze_segment(segment))

    target_findings: list[TargetFinding] = []
    for op in operations:
        for target in op.targets:
            if op.operation == "npm package uninstall":
                target_findings.append(
                    TargetFinding(
                        target=target,
                        normalized=target,
                        risk="medium",
                        label="Package-manager target",
                        at_stake=["The named package or global CLI binary, not the tool's user-data directories."],
                        scenarios=["An uninstall command can be safe by itself, but pairing it with rm -rf against config/state paths changes the risk boundary."],
                        safer=["Run the package uninstall separately from any data cleanup."],
                    )
                )
            else:
                target_findings.append(classify_target(target))

    risk = "low"
    for op in operations:
        risk = max_risk(risk, op.risk)
    for target in target_findings:
        risk = max_risk(risk, target.risk)

    return {
        "command": command,
        "risk": risk,
        "operations": [op.__dict__ for op in operations],
        "targets": [target.__dict__ for target in target_findings],
    }


def render_text(result: dict) -> str:
    lines: list[str] = []
    risk = result["risk"].upper()
    lines.append(f"Risk: {risk}")
    lines.append(f"Command: {result['command']}")
    lines.append("")

    if not result["operations"]:
        lines.append("No known destructive operation was detected, but review the target and flags before running.")
        return "\n".join(lines)

    lines.append("Operations:")
    for op in result["operations"]:
        lines.append(f"- {op['operation']} ({op['risk']}) targets: {', '.join(op['targets'])}")
        for note in op["notes"]:
            lines.append(f"  note: {note}")

    lines.append("")
    lines.append("Target synopsis:")
    seen: set[str] = set()
    for target in result["targets"]:
        key = f"{target['target']}|{target['label']}"
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {target['target']} -> {target['label']} ({target['risk']})")
        lines.append(f"  at stake: {'; '.join(target['at_stake'])}")
        lines.append(f"  scenario: {'; '.join(target['scenarios'])}")
        lines.append(f"  safer: {'; '.join(target['safer'])}")

    lines.append("")
    if result["risk"] in {"critical", "high"}:
        lines.append("Approval question:")
        lines.append("Do you want to run this exact destructive command against this exact target, knowing the data at stake above, or should I use the safer inspection/backup path first?")
    else:
        lines.append("Approval question:")
        lines.append("Should I inspect the target first, then run the command only if it matches the expected disposable files?")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review command plus target risk without executing it.")
    parser.add_argument("--command", "-c", help="Command string to review. If omitted, read stdin.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    command = args.command
    if command is None:
        command = os.sys.stdin.read().strip()
    if not command:
        parser.error("provide --command or pipe a command on stdin")

    result = analyze(command)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
