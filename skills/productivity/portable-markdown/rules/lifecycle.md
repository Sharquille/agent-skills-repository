# Lifecycle Markdown House Style

<!-- portable-markdown:lifecycle-house-style -->

This rule set applies to disk-backed lifecycle notes produced by
`project-build-loop`: task notes, observations, steps ledgers, consult summaries,
reference registries, and publish handoff notes. It extends the base portable
Markdown standard; it does not replace it.

## Goals

- Keep working notes readable in GitHub, Obsidian, VS Code, and static-site
  pipelines.
- Make lifecycle state unambiguous: a closed task must not also tell the user it
  is open.
- Keep task notes as the low-noise action surface and steps ledgers as the method
  record.
- Prevent stale routed work from remaining in the wrong task checklist.

## Severity

- **Error**: blocks checkpoint, consult, and publish handoff until fixed.
- **Warning**: report and usually fix before the next user-facing update, but do
  not block raw working notes.
- **Info**: style suggestion only.

## Error Rules

- **base-portability**: The base `portable-markdown/scripts/lint.sh` must pass.
- **contradictory-task-state**: A file that says `Status: DONE`, `Status: done`,
  or `Status: closed` must not also say the task `remains open` or keep an
  unchecked `Explicitly say task ... ready to close` closure item.
- **missing-task-status**: `build-log/task-N.N*.md` files must contain a
  `## Status` section and a `Status:` line.
- **stale-route-action**: If work is routed to a future task, the current task
  note must say `routed to task N.N` or `tracked under task N.N`; it must not
  present the same routed item as an unchecked local action.
- **broken-table-row**: Markdown table rows must have the same number of cells as
  their header row after escaped pipes are ignored.

## Warning Rules

- **table-overuse**: More than three tables in a focused task note is a warning.
  Ledgers may use more tables because their job is structured evidence.
- **heading-level-skip**: Do not jump from `##` to `####` without `###`.
- **long-checklist**: More than ten checklist items in a focused task note is a
  warning; split action items from evidence records.

## Gate Integration

`project-build-loop` should run the lifecycle lint only on Markdown files touched
by the current phase or explicitly selected for cleanup.

- **Task note / steps update**: run before checkpoint. Errors block checkpoint.
- **Consult**: run before sending artifacts. Errors block consult; warnings are
  logged.
- **Publish handoff**: run on every Markdown artifact entering `publish/`. Errors
  block handoff.
- **Observations during exploration**: do not block raw capture at write time.
  Run the gate when observations are promoted, routed, consulted, or published.

## Project-Build-Loop Task Board

Use `build-log/tasks.md` as the primary task surface. It should read like a
plain sequential board: done, current blocker, next input, routed follow-up, and
close condition. Do not create a separate `task-N.N.md` summary for every task.
Use `build-log/task-N.N.steps.md` only for reproducible method and evidence.

## House Style

- Start `build-log/tasks.md` with project status, then list tasks in sequence.
  Each task section should show status, current blocker or next action, evidence
  pointers, and close condition.
- Put actual commands, persistence files, issue/fix rows, and validation evidence
  in `build-log/task-N.N.steps.md`, not the task note.
- Use task notes for current action, accepted/pending/rejected defaults, routed
  advisories, and close conditions.
- Do not leave historical correction noise in the action surface. Move rationale
  to observations or the steps ledger once the current state is clear.
- Prefer compact prose and tight bullets for explanation. Use tables for real
  matrices, evidence ledgers, or checklists where columns add clarity.
- Every routed item must name the owning task and its status there.
