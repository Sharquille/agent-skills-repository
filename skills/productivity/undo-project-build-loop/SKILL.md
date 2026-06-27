---
name: undo-project-build-loop
description: "Safely undo or roll back project-build-loop actions: a mistaken project bootstrap, a wrong-category scaffold, a false-start project, or a checkpoint that needs reverting. Use when the user wants to remove a generated project tree, clear or repoint the global last-active pointer, reverse a recorded task checkpoint, or preview what an undo would remove. Always inventory and dry-run first; shares the conductor's manifest/checkpoint machinery and never invents deletion steps. Do not trigger for deleting normal files unrelated to a project, or for reverting study-loop state (use undo-obsidian-study-loop)."
# --- provenance ---
category: productivity
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Undo Project Build Loop

The rollback companion to `project-build-loop`. It reverses **recorded** actions
using the conductor's own manifest and `event-log.jsonl` — it does not improvise
deletions. Always inventory and dry-run before removing anything.

## Prime directives

1. **Inventory first.** Read `project.json`, `event-log.jsonl`, and the bootstrap
   created-files manifest. Show exactly what exists and what would change.
2. **Dry-run by default.** Print the plan; only act on explicit confirmation.
3. **Reverse recorded state only.** Roll back to a checkpoint's `rollback_point`
   (git sha) or remove only files the bootstrap manifest recorded creating.
4. **Never touch evidence/secrets without explicit confirmation.** `evidence/`
   and `.vault/` may hold the only copy of authorization records or hashes.

## Common undos

- **Mistaken bootstrap / wrong category** — verify the project tree was created
  by `bootstrap_project.sh` (has a seed `project.json` + matching event-log
  bootstrap line and is otherwise empty of your real work), then remove it and
  clear the global `last-active.json` pointer.
- **False-start task** — `git` reset to the task checkpoint's `rollback_point`;
  mark the task `todo`; append an undo entry to `event-log.jsonl`.
- **Repoint active project** — set `_index/last-active.json` to a different
  project without deleting anything.

## Safety

- A reviewed/active project stays on disk unless the user explicitly asks to
  delete it. Confirm the tree is a genuine false start (no real build-log/evidence
  work) before removal.
- Keep `event-log.jsonl` append-only — record the undo as a new event; do not
  rewrite history.
- If anything is ambiguous (real work present, unknown provenance), stop and ask.
