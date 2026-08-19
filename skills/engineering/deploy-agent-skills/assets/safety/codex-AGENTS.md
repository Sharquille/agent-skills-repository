# Global Codex Safety Rules

Before proposing or running destructive filesystem commands, explain the exact paths, what user data could be lost, safer alternatives, and the verification step. Wait for explicit approval for the exact command.

Use the `command-risk-review` skill when a request combines a command with a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

Never delete or recursively remove `~/.claude`, `~/.config/claude`, `~/.local/share/claude`, `~/Library/Application Support/Claude`, `~/.agents`, `~/.codex`, `~/.gemini`, or `{{REPO_DIR}}` from an agent session.

Uninstalling a CLI is not approval to delete user data, project history, transcripts, settings, or skills. Prefer package-manager uninstall commands and inspect paths before changing them.

## Writing standard

For authoring and handover, follow the repository's preservation-first standards:

- `anti-slop-standard` owns code authoring, scope, tests, and the handover check.
- `unslop` is always-on for prose, but does not rewrite technical terms, required wording, exact commands, identifiers, or unchanged sentences mechanically.
- Treat delegated output as a draft until it passes the handover check.

The standards do not override user instructions, required legal or security wording,
technical precision, or established repository terminology. Load the full standards
from:

- `{{REPO_DIR}}/skills/engineering/anti-slop-standard/SKILL.md`
- `{{REPO_DIR}}/skills/productivity/unslop/SKILL.md`
