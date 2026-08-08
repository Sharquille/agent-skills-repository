---
name: reasoning-gym
description: Short, repeatable, interleaved practice reps on the reasoning moves already taught once by reasoning-moves — a spaced-retrieval maintenance coach, not a first-teaching skill. Reads reasoning-moves' TRACE loop and five move-decks (language, quantitative, inference, conceptual, calibration) by name rather than duplicating them, picks a small mixed-substrate set weighted toward moves marked fragile or stale, and hands each rep to teach-complex-concepts to actually run — this skill never reimplements its hint ladder, response classification, or mastery judgment. Owns one piece of state neither of those skills provides — a lightweight cross-session ledger of which moves are secure vs. fragile and when each was last practiced. Use on request — "give me a reasoning warm-up," "drill me on reasoning moves," "quick reasoning practice," "spaced practice," "check if X is still secure," "interleave some reasoning reps" — or proactively suggest it when a move in the ledger has gone stale and the user is between other tasks. Do not trigger to teach a reasoning move for the first time (use reasoning-moves) or for single-topic subject tutoring (use teach-complex-concepts).
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-08-08
---

# Reasoning Gym

A spaced-practice coach for the moves `reasoning-moves` already taught. Its
only job is picking *what* to practice next and remembering *how it went
last time* — it holds no tutoring logic of its own and no duplicate copy of
the curriculum.

## Core stance

- This skill is pure orchestration plus one small ledger. The move-decks,
  diagnostic cases, and the TRACE loop all live in `reasoning-moves` —
  always read them from there by name; never copy or fork them into this
  skill's own files.
- `teach-complex-concepts` still runs every actual rep: diagnose, act,
  respond to evidence, hint ladder, consolidate, judge mastery. This skill's
  contribution is *selecting* the case and *recording* the outcome, not
  tutoring.
- A rep set is short by design — 3 to 6 cases, a few minutes each. If the
  learner wants a full first-teaching session on a move, hand off to
  `reasoning-moves` instead of stretching a rep set to cover it.
- Favor durability over novelty: repeating a move the ledger marks fragile
  is more valuable than always picking something new.

## The ledger

The one piece of state this skill owns: a single Markdown file that starts
with only the header row below and gains one row per move the first time
that move is actually practiced here — never pre-populated for every move in
`reasoning-moves`, and never a row for a move that hasn't been taught yet
(see "Run a rep set," step 1).

```markdown
| Move | Deck | Last practiced | Status | Streak |
|---|---|---|---|---|
| Correlation vs. causation | inference | 2026-08-08 | secure | 3 |
| Definition hygiene | language | 2026-07-30 | fragile | 0 |
```

- **Status** is a *rep-outcome* tracker, deliberately coarser than and
  distinct from `teach-complex-concepts`' own five-level mastery scale
  (`unassessed` → `emerging` → `developing` → `secure` → `transfer-ready`,
  which stays session-scoped there unless persisted through an
  `obsidian-study-loop` dive) — this ledger tracks "how did the last one or
  two reps on this move go," not full mastery:
  - `fragile` — the most recent rep closed as anything other than an
    independent, correct-and-reasoned success: `correct but fragile`,
    `productive error`, `guess or misconception`, `repeatedly stuck`, or
    `overloaded/frustrated` in that skill's own classification. Resets
    streak to 0.
  - `secure` — only after **two consecutive** independent,
    correct-and-reasoned closes, mirroring that skill's own rule to advance
    mastery only after at least two non-identical successful checks. One
    good rep is progress, not security.
- **Streak** — consecutive independent, correct-and-reasoned closes; reset
  to 0 on any other outcome.
- **Stale** — no row update in 14+ days. Treat a stale `secure` row as worth
  one confirming rep before trusting the streak further.
- Update one row per rep, immediately after `teach-complex-concepts` closes
  it out, from its own response classification — never invent an outcome the
  engine didn't actually classify, and never skip the update.

**Location.** Resolve once per environment, cheapest first:

1. If the user has already named a path earlier in this conversation, use it.
2. If an `obsidian-study-loop` vault session is active, offer
   `_study/reasoning-gym-ledger.md` inside that vault — but this ledger is
   cross-topic and outlives any single study session, so it is this skill's
   file, not a dive note.
3. Otherwise default to `~/.reasoning-gym/ledger.md`, creating the parent
   directory (`mkdir -p ~/.reasoning-gym`) if needed, and say which path was
   chosen once so the user can redirect it.

If the ledger file doesn't exist yet, create it with only the header row —
rows accrue as moves are actually practiced, per above.

## Run a rep set

1. **Read the ledger.** If it has no rows yet, nothing has been practiced
   here before, so this skill has nothing to drill: say so, and either hand
   off to `reasoning-moves` for a first session, or — if the learner says
   they've already covered specific moves elsewhere — start with those,
   adding each a row only once it is actually practiced here, never
   pre-populated on the strength of a claim.
2. **Select 3-6 cases**, weighted by ledger state:
   - Prioritize `fragile` moves and anything unpracticed for a long stretch.
   - Interleave decks — never run all reps from one deck in a row; mixing
     substrates is what makes this spaced *and* interleaved practice rather
     than a single-topic drill.
   - Occasionally include a `secure` move anyway, to confirm it's still
     durable rather than assuming a past streak holds forever.
3. **For each case**, read the case and its move from the relevant
   `reasoning-moves` deck file, then hand off to `teach-complex-concepts`
   exactly as `reasoning-moves` would for a first teaching turn — same
   handoff contract (learning target, diagnostic case, the move as the Apply
   principle), except do not re-teach TRACE from scratch; assume the learner
   already has it and reference it by name ("run TRACE on this one").
4. **After each case closes**, update that move's ledger row per the Status
   rule above — `secure` only on a *second consecutive* independent,
   correct-and-reasoned close; any other classification marks `fragile` and
   resets the streak. Do not silently skip a ledger update.
5. **Close the set** with a one-line summary: which moves firmed up, which
   are still fragile, and — only if asked, or if several moves are fragile —
   a suggestion to run a full `reasoning-moves` session on the weakest one
   instead of another rep set.

## What this skill never does

- Never invents a diagnostic case that doesn't exist in `reasoning-moves` —
  if the right case isn't there, that's a signal to add it there (or run
  `reasoning-moves` directly), not to improvise content here.
- Never reimplements hint ladders, mastery judgment, or response
  classification — those stay in `teach-complex-concepts`.
- Never treats a ledger streak as a permanent trait; a long streak makes a
  move *lower priority* for the next rep set, not exempt from ever being
  re-checked.
