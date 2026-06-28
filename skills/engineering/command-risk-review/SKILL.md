---
name: command-risk-review
description: "Review a shell command, CLI action, API endpoint action, or destructive operation together with its target path/resource before execution. Use when a user asks whether a command is safe, asks to run cleanup/uninstall/delete/reset commands, mentions rm -rf, find -delete, git reset, git clean, curl DELETE, cloud delete operations, cache/config cleanup, or any command targeting agent state such as .claude, .agents, .codex, .gemini, skills, projects, transcripts, Obsidian vaults, repositories, or app support data."
---

# Command Risk Review

Use this skill to produce a target-aware risk review before a command is run. Do not judge a command by verb alone: `rm -rf node_modules` and `rm -rf ~/.claude` are both deletes, but only one normally removes project history, skills, settings, and transcripts.

## Workflow

1. Identify the operation and the target.
   - Operation: delete, uninstall, reset, clean, overwrite, move, chmod/chown, API DELETE, cloud recursive remove, etc.
   - Target: local path, glob, package name, URL endpoint, cloud resource, app data folder, repository, or vault.
2. Run the helper when the request includes a shell-like command:
   ```text
   python3 scripts/command_risk_review.py --command 'rm -rf ~/.claude/*'
   ```
3. Read `references/protected-targets.md` when the target is a dotfile/dotdir, agent folder, app support folder, repository, vault, wildcard, or endpoint/resource you do not recognize.
4. Inspect the target read-only when local access is available:
   - Prefer `ls -la`, `find <target> -maxdepth 2 -print`, `du -sh`, `file`, `readlink`, and `git status`.
   - Do not mutate, move, truncate, chmod, chown, or delete during risk review.
   - If the command contains a glob, inspect both the literal pattern and its likely expansion.
5. Produce a short but concrete synopsis:
   - Verdict: safe to run, ask first, do not run, or needs more inspection.
   - Command and target summary.
   - What could be lost, including project history, transcripts, skills, settings, credentials, symlink targets, caches, local DBs, and app support data.
   - Realistic failure scenarios.
   - Safer alternative and verification command.
   - Exact approval question if user approval is required.

## Review Standard

Treat these as high-risk even when the user asks casually:

- Recursive deletes: `rm -rf`, `rm -fr`, `find ... -delete`, `find ... -exec rm`.
- Hidden bulk globs: `.*`, `.[!.]*`, `..?*`, `.*/`, or any broad dotfile cleanup.
- Agent and app state: `.claude`, `.agents`, `.codex`, `.gemini`, Claude Desktop app support, OpenCode config/state, skills folders.
- History stores: `projects`, `sessions`, `transcripts`, `logs`, SQLite DBs, JSONL files.
- Repository internals: `.git`, `.github`, hooks, worktrees, ignored-but-important local files.
- Vaults and sync folders: Obsidian, iCloud, Dropbox, Google Drive, notes, study folders.
- API/cloud destructive actions: HTTP `DELETE`, recursive bucket/object removal, database drops, IAM/policy deletion.

## Output Shape

Keep the answer compact and actionable:

```text
Verdict: Do not run as written.

Command: rm -rf ~/.claude/*
Target: ~/.claude is Claude Code user state, not just the npm CLI package.
At stake: skills, project JSONL transcripts, settings, MCP/session state, and recovery metadata.
Scenarios: Claude can lose prior project conversations; OpenCode can lose skill discovery if it relied on ~/.claude/skills; rm bypasses Trash.
Safer path: uninstall the package only, then inspect ~/.claude before deciding whether to archive anything.
Approval question: Do you want to delete Claude user data at ~/.claude, or only uninstall the npm CLI?
Verification: which claude || true; find ~/.claude -maxdepth 2 -type f | head
```

## Safe Defaults

- Use package-manager uninstall commands without deleting user data unless the user explicitly approves the data deletion path.
- Prefer timestamped backups or quarantine moves over deletes for configuration and app data.
- Prefer read-only evidence before risk claims. When making an inference, name it as an inference.
- If a command combines a low-risk operation with a high-risk cleanup, split the command and ask about the high-risk part separately.
