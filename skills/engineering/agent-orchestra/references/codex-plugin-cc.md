# Optional Codex Plugin For Claude Code

Source: https://github.com/openai/codex-plugin-cc, researched 2026-07-02.
Upstream version observed: `1.0.5` (`v1.0.5`, latest release shown 2026-06-23).
License: Apache-2.0 upstream. This reference is a local operational summary,
not a vendored copy of the plugin.

## Wrapper-First Position

Use wrappers first in this repository. The plugin is useful if it is already
installed in Claude Code, but it is not required and should not block work. The
portable path is:

```text
scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
scripts/codex-agent.sh review --uncommitted
scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> -- "<task>"
```

## What The Plugin Provides

The official OpenAI Claude Code plugin lets Claude Code users call Codex from
inside Claude Code. It uses the local `codex` binary, local Codex auth, local
Codex app server, and the same Codex configuration.

Main commands:

- `/codex:review`: normal Codex review of uncommitted work or branch diff. It is
  read-only and does not fix code.
- `/codex:adversarial-review`: steerable read-only review that challenges the
  implementation, design, assumptions, and risk areas.
- `/codex:rescue`: delegates a task to Codex through a thin Claude subagent and
  the companion runtime. This can be write-capable unless explicitly constrained.
- `/codex:transfer`: imports the current Claude Code session into a persistent
  Codex thread and prints a `codex resume <session-id>` command.
- `/codex:status`, `/codex:result`, `/codex:cancel`: manage background Codex
  jobs.
- `/codex:setup`: checks local Codex readiness and can enable/disable the
  optional stop-time review gate.

## Requirements

- ChatGPT subscription, including Free, or an OpenAI API key.
- Node.js 18.18 or later.
- The local Codex CLI installed and authenticated.

## Install In Claude Code

Run these inside Claude Code, not in a shell:

```text
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

If Codex itself is missing and the plugin cannot install it, install Codex in a
shell:

```text
npm install -g @openai/codex
codex login
```

## Safe Command Choices If Installed

Use `/codex:review --background` for ordinary code review. Review can take a
while, especially on multi-file changes.

Use `/codex:adversarial-review --background <focus>` when the user wants a
challenge review, such as auth, data loss, rollback, race conditions, caching,
or reliability.

Use `/codex:rescue` for delegation, not for a normal review. Scope the task,
state whether writes are allowed, and prefer an isolated branch/worktree for
substantial write-capable work. The upstream rescue subagent defaults to adding
`--write` unless the request is explicitly read-only or review-only.

Use `/codex:transfer` when a Claude Code conversation should continue in Codex.
The plugin expects the source transcript under `~/.claude/projects`.

Use the optional review gate only while actively monitoring the session. The
upstream README warns that stop-gate review can create long Claude/Codex loops
and consume usage quickly.

## Codex Configuration

The plugin inherits Codex configuration. To set a project default model or
reasoning effort, use `.codex/config.toml` in a trusted project or
`~/.codex/config.toml`:

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

For this repository's orchestration defaults, do not hardcode `gpt-5.5` in the
skill body. Let Codex use the user's config default unless the user explicitly
asks for a model override.

## Safety Notes

- `/codex:review` and `/codex:adversarial-review` are read-only.
- `/codex:rescue` is delegated task execution and can write. Require clear scope.
- Plugin output is still model output. The conductor verifies before acting.
- Prompts and repository context may egress to OpenAI. Do not include secrets.
- Background runs should be checked with `/codex:status` and `/codex:result`.
