---
name: resolving-merge-conflicts
description: "Work through an in-progress git merge or rebase conflict hunk by hunk: read each side's original intent from commits, PRs, and issues, preserve both intents where they are compatible, then run the project's checks and finish the operation. Use when a merge, rebase, or cherry-pick has stopped on conflicts, or when a rebase needs continuing to completion. Do not trigger for planning a merge strategy before starting, or for reviewing an already-clean diff (use code-review)."
# --- provenance ---
category: engineering
source: https://github.com/mattpocock/skills/tree/main/skills/engineering/resolving-merge-conflicts
author: Matt Pocock (mattpocock/skills)
license: MIT
retrieved: 2026-08-19
modified-by: Sharquille Andrew (description expanded to this repo's trigger/anti-trigger convention; uncommitted-work guard added)
---

1. **See the current state** of the merge/rebase. Check git history, and the conflicting files.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made, and what the original intent was. Read the commit messages, check the PRs, check original issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour. If the user wants to abort, review that choice and its impact rather than assuming resolution is required.

4. Discover the project's **automated checks** and run them — typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage only reviewed files and commit when the user has asked to complete the operation. If rebasing, continue the rebase process only with that intent confirmed.

## Local guard

Before any command that could discard work — `git checkout`, `restore`, `reset`, `clean`, `stash drop`, or `merge --abort` — run `git status`, inventory untracked files, and preserve them with `git stash -u` or a reviewed copy before changing state. Route anything destructive through `command-risk-review`. Review what a broad `git add` staged before committing; a conflicted tree is where stray backup files and editor droppings get swept in.
