# Sol review

Every section build gets an independent read-only review from Sol through
`agent-orchestra` before its notebook is built. The reviewer reads only what
the brief carries; the conductor checks every finding against the ledger and
sources, applies what holds up, and records the result. Sol is advisory: it
never edits the kit.

## When

After the editorial review (step 6) and `validate_kit.py --section`, before
the notebook build (step 7). Run it for every new or rewritten Core, in any
course, Monroe University included: the brief carries study notes, never
graded work, credentials, or local file paths. A typo-level fix (one word, a
broken link) does not need a new review.

## How

```sh
ORCH=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/engineering/agent-orchestra/scripts
REVIEW=$(mktemp -d)
python3 "$SKILL_DIR/scripts/review_brief.py" --section "$SECTION" > "$REVIEW/brief.txt"
# A rewrite also passes the previous Core: --before "$OLD_NOTES"
"$ORCH/codex-agent.sh" consult --model gpt-6.1-sol --effort xhigh --cd "$REVIEW" \
  --timeout 1200 -- "$(cat "$REVIEW/brief.txt")" > "$REVIEW/sol.md" 2> "$REVIEW/sol.log"
```

- **Model:** Sol 6, `gpt-6.1-sol` (the Codex default in `~/.codex/config.toml`).
  If a newer Sol replaces it there, use that one. Never Haiku, and never the
  model that wrote the notes.
- **Effort:** `xhigh`. The job is careful comparison, not long computation.
- **Several sections:** run one call per section in parallel (Codex calls do
  not share state), each with its own brief and output file.
- **Codex unavailable** (rate limit, outage, repeated timeout): fall back to
  the `agent-orchestra` OpenCode ladder (`--lane reasoning`), say so in the
  summary, and leave `review` pending until Sol has run.

`review_brief.py` sends the ledger from **Earned** on (its source table holds
local paths), the Practice question titles, each figure's printed labels, and
the Core. It asks for five lists: unsupported claims, lost facts, changed
meaning, repetition inside one heading, and technical errors.

## Judging the findings

Treat the output as untrusted. For each finding:

- **Accept** when the ledger, the source page, or an authoritative reference
  confirms it. Fix the Core, and the ledger when a cut moves detail.
- **SOURCE CONFLICT** findings (the ledger shows the course itself says it):
  keep the course wording, verify the correction against an authoritative
  reference, add a short `> [!NOTE]` correction at the heading, and record it
  in the ledger's Uncertain (or Corrections) list.
- **Reject** when it asks to reprint Tier 3 detail the ledger's Context list
  already holds, to reprint a figure's labels as prose, or to drop a TEST MOVE
  that names its concept as a scenario clue.
- An exam-frequency phrase ("most often confused," "classic") is always a
  finding: HIGH YIELD states signals, not predictions.

Rerun `validate_kit.py --section` after the fixes. Rerun Sol only when a fix
rewrites a heading's meaning, not for wording repairs.

## Record it

In `state.json`, set `verification.review` to `passed` once the findings are
resolved, and add `review_note` with the date, the model, and the count of
accepted and rejected findings:

```json
"verification": {"local": "passed", "render": "passed", "review": "passed", "import": "pending"},
"review_note": "2026-10-08 gpt-6.1-sol xhigh: 6 accepted, 9 rejected (TEST MOVE clues, Context-list detail)"
```

A section with a `revised` date cannot be `complete` until `review` is
`passed`; `validate_kit.py --kit` warns while it is pending.
