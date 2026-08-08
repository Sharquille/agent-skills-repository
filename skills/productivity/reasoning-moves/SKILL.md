---
name: reasoning-moves
description: Build foundational, cross-domain reasoning and perception skills — the substrate underneath any single subject, spanning precise language (English), quantitative intuition (Math), logical inference (Reasoning/Logic), conceptual distinctions (Philosophy), and calibrated judgment. Supplies a domain-general reasoning loop (TRACE) plus five tagged move-decks and diagnostic cases; teach-complex-concepts runs the actual tutoring turn — this skill never reimplements its hint ladder, response classification, or mastery judgment. Use when a learner wants to get better at how they reason or perceive in general, not learn one topic — trigger after an answer reveals a reasoning slip (treating a hypothesis as a fact, correlation as causation, an assumption as established, an ambiguous term as precise), or on request — "build my intuition," "sharpen my reasoning," "think more clearly," "help me choose words more precisely," "teach me to argue/estimate/judge confidence better." When an obsidian-study-loop vault session is active and the gap is relevant, this skill self-detects it and runs session-integrated as a teaching dive under teach-complex-concepts' own Mid-Session Deep Dives rules. Do not trigger for single-topic subject tutoring with no cross-domain reasoning angle (use teach-complex-concepts directly), for spaced/interleaved review of moves already taught once (use reasoning-gym), or for formal curriculum documents.
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-08-08
---

# Reasoning Moves

A content library for the thinking moves that sit underneath any single
subject: how to read a claim precisely, estimate a quantity, judge whether an
inference holds, draw a conceptual distinction, and calibrate confidence. It
exists because `teach-complex-concepts` is a domain-agnostic tutoring
**engine** with no built-in curriculum — it needs a topic and diagnostic
material handed to it. This skill is that material for the reasoning
substrate specifically.

## Core stance

- This skill supplies **what** to teach (a diagnostic case, the relevant
  loop step or move, a practice set). `teach-complex-concepts` owns **how**
  the turn runs — diagnose, build the model, make the learner act, classify
  the response, hint ladder, consolidate, judge mastery. Never reimplement
  any of that here; hand off and let it run.
- Teach one universal loop, not one loop per problem type. The loop (TRACE,
  below) is domain-general and gets reused on every case. Substrate-specific
  content is a small set of **moves** that plug into one or two loop steps —
  they are not separate loops.
- A move is teachable only if it is falsifiable and checkable in the
  learner's own answer — "notice framing" is not a move; "flag when a
  question's wording presupposes the answer it wants" is.
- Treat a wrong answer as evidence of which move is missing, not as failure.
  The diagnostic cases in `references/moves/` are chosen because they have an
  informative wrong answer, mirroring the store-sign / laptop-slowdown style
  that motivated this skill.

## The meta-loop: TRACE

Every session anchors on one compact, reusable loop:

- **T — Target**: what is the question actually asking?
- **R — Record**: what facts are directly given?
- **A — Apply**: what principle connects those facts to an answer?
- **C — Check**: what assumptions, alternatives, or edge cases matter?
- **E — Express**: state the strongest conclusion the evidence supports.

Read [meta-loop.md](references/meta-loop.md) for the worked example and for
how each substrate's moves plug into Check and Apply specifically. Teach
TRACE explicitly and by name the first time a learner works a case with this
skill; after that, invoke it by name ("run TRACE on this") rather than
re-explaining it.

## The five move-decks

| Substrate | Implicated when the learner... | Reference |
|---|---|---|
| Language | mishandles a definition, conflates denotation/connotation, overclaims with an unhedged verb, misses a presupposition or framing effect | [moves/language.md](references/moves/language.md) |
| Quantitative | needs an order-of-magnitude estimate, confuses a rate with a total, or takes a noisy extreme at face value | [moves/quantitative.md](references/moves/quantitative.md) |
| Inference | treats correlation as causation, argues invalidly, can't name the alternative explanation, or can't say what would falsify their claim | [moves/inference.md](references/moves/inference.md) |
| Conceptual | conflates necessary and sufficient conditions, can't define a term by its distinguishing feature, or argues against a weakened version of the other side | [moves/conceptual.md](references/moves/conceptual.md) |
| Judgment & calibration | states confidence disconnected from evidence, anchors on the first number seen, or doesn't reserve belief for what evidence supports (the trained *output* of the other four decks, not a sibling topic) | [moves/calibration.md](references/moves/calibration.md) |

More than one deck is often implicated by a single case — say so rather than
forcing one label.

## Run the session

1. **Identify the substrate(s).** From the learner's question or a wrong
   answer, name which deck(s) apply. If none of the five fit, this isn't a
   reasoning-moves case — teach the topic directly or route to
   `teach-complex-concepts` with no diagnostic material attached.
2. **Pick or improvise one diagnostic case.** Prefer a case from the relevant
   `references/moves/*.md` file; when none fits the learner's context closely
   enough, write a new one in the same style (a short scenario with a
   tempting-but-wrong first-pass answer) rather than forcing a mismatched
   stock case.
3. **Hand off to `teach-complex-concepts`.** Give it: the learning target
   stated in observable terms ("distinguish an observed fact from an invented
   explanation in a causal claim"), the diagnostic case, and the specific
   move(s) from the relevant deck as the "principle" for its Apply step. Let
   it run its full adaptive workflow — diagnose, model, act, respond, hint
   ladder, consolidate, judge mastery — unmodified. This skill's job ends at
   the handoff.
4. **Name the loop and the move explicitly during consolidation** so the
   learner leaves with a labeled, reusable tool ("that was TRACE's Check step
   — controlled comparison") rather than a one-off insight.
5. For repeated, spaced, or interleaved practice on moves already taught once
   — as opposed to first teaching them — use `reasoning-gym` instead; it
   reads this skill's move-decks by name rather than duplicating them.

## Study-session integration

Mirrors `teach-complex-concepts`' own pattern exactly — this skill adds no
new persistence or session rules of its own. When invoked while an
`obsidian-study-loop` vault session is active and the reasoning gap is
relevant to that session, run as a teaching dive under that protocol: resolve
the vault, relevance-check the topic (`in-scope` / `adjacent` / `unrelated`),
then hand off to `teach-complex-concepts` per step 3 above so persistence
(dive entry, decoupled dive note, session-log line) happens exactly as it
would for any other teaching dive. Never invent separate persistence here.
Outside a vault session, this skill persists nothing — the learning state
lives in the conversation and, at close, in `teach-complex-concepts`'
end-of-session summary.

## Correctness gates

- Verify each diagnostic case actually has an informative wrong answer before
  using it — a case where the "tempting" answer is also defensible teaches
  nothing.
- For the conceptual and language decks, several moves touch contested
  philosophical or linguistic territory (e.g., where vagueness shades into
  ambiguity, is/ought). Teach the distinction and the disagreement among
  serious treatments of it; do not present a contested position as settled.
- For the calibration deck, verify any cited numeric claim (base rate,
  probability) before using it in a case; do not invent statistics to make a
  case land.
