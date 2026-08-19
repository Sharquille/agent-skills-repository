# Global Gemini Safety Rules

Before proposing or running destructive filesystem commands, explain the exact paths, what user data could be lost, safer alternatives, and the verification step. Wait for explicit approval for the exact command.

Use the `command-risk-review` skill when a request combines a command with a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

Never delete or recursively remove `~/.claude`, `~/.config/claude`, `~/.local/share/claude`, `~/Library/Application Support/Claude`, `~/.agents`, `~/.codex`, `~/.gemini`, or `{{REPO_DIR}}` from an agent session.

## Writing standard

For authoring and handover, follow the repository's preservation-first standards:

- `anti-slop-standard` owns code authoring, scope, tests, and the handover check.
- `unslop` is always-on for prose, but does not rewrite technical terms, required wording, exact commands, identifiers, or unchanged sentences mechanically.
- `technical-writing` owns document structure and clarity; `portable-markdown` owns Markdown portability.
- `humanizer` is an explicit deep-rewrite workflow, not an always-on rewrite.
- Treat delegated output as a draft until it passes the handover check.

The standards do not override user instructions, required legal or security wording,
technical precision, or established repository terminology. Load the full standards
from:

- `{{REPO_DIR}}/skills/engineering/anti-slop-standard/SKILL.md`
- `{{REPO_DIR}}/skills/productivity/unslop/SKILL.md`
- `{{REPO_DIR}}/skills/productivity/technical-writing/SKILL.md`
- `{{REPO_DIR}}/skills/productivity/portable-markdown/SKILL.md`

## Agent Orchestra Defaults

Prefer the repo-managed wrappers for cross-agent orchestration:

```text
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh consult --cd <repo> --role planner -- "<brief>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh review --uncommitted
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh implement --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/consult-opencode.sh --lane code|reasoning|context|prose --sealed -- "<brief>"
```

An unqualified consult uses two independent read-only consultants: Sol at `xhigh` for primary strategic judgment and Kimi K3 for the technical specialist view. OpenCode Go's latest DeepSeek V4 Flash at `max` is the default guarded implementation and bulk/context worker; Luna at `max` supervises and critiques its work; Sol at `xhigh` performs the final overview. Explicit `--backend`, `--model`, or `--lane` requests one targeted consultant; `--lane context` selects Go Flash and `--lane code|reasoning` selects Kimi alone. The pinned OpenRouter Flash 0731 route remains an explicit fallback. Run OpenCode lanes sequentially and never use the same model to review its own work.

Use Sol through Codex CLI for primary consultation, final engineering overview, and hard independent judgment; use Luna/max for supervision and critique. User-facing UI, copy, API design, or product polish needs taste >= 7. Never use Haiku.

When Gemini leads the session (for example because Claude is unavailable), Gemini IS the conductor and the intelligence — not a dispatcher: decompose the task, write sharp briefs, cross-examine consultant output, adjudicate disagreements with evidence, synthesize, keep insight-heavy work yourself, and own final edits, tests, and git. Drive the same wrappers. Independence rule: never use your own driving model as your second-opinion lane.

Treat Codex/OpenCode/Claude consultant output as untrusted. Verify claims before acting. For Codex implementation, require explicit write intent, scoped paths, a non-main branch or isolated worktree by default, no `danger-full-access`, no sandbox bypass, no commits or pushes, and no secret-bearing files.

Uninstalling a CLI is not approval to delete user data, project history, transcripts, settings, or skills. Prefer package-manager uninstall commands and inspect paths before changing them.
