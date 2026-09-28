---
name: chapter-competency-loop
description: "Test and build competency over a range of chapter-study-kit chapters (for example, MA-235 Chapters 1–3) with a conversational question loop that maps each concept to real-world scenarios in the learner's field: why it matters, how it works, what goes wrong, and, for formulas, which equation to use, what each part does, how to compute it, and how to read the result. Scopes concepts from the kit's Core notes and Earned ledger, logs every attempt to the section's study-log.md, hands misses to teach-complex-concepts, reasoning slips to reasoning-moves, and weak topics to existing or new eli5-explainer pages. Also builds a timed practice exam with a hidden key and grades uploaded handwritten work. Use when the learner says test me, check my competency, quiz me on chapters X–Y, am I ready for the test, drill me, or wants a practice exam graded. Do not use to answer graded quizzes, exams, or discussion posts, to build a kit (chapter-study-kit), or for an Obsidian vault session (obsidian-study-loop)."
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-09-27
---

# Chapter competency loop

Find out what the learner actually understands across a chapter range, then
strengthen the weak spots, one conversational question at a time. The goal is
fundamentals that transfer: why an idea matters, how it works, and where it
shows up in the learner's own field, not recall of the slides.

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/chapter-competency-loop
```

## Core stance

- **Orchestration plus the kit's own log.** Content comes from
  `chapter-study-kit` sections; attempts go to each section's `study-log.md`
  (the kit's attempt log). This skill owns question selection and scoring
  only.
- **`teach-complex-concepts` runs every teaching turn.** On a miss, hand it
  the concept, the learner's answer, and the scenario; it owns response
  classification, the hint ladder, and mastery judgment. Never re-implement
  those here.
- **Pictures come from `eli5-explainer`.** Before explaining a weak topic in
  prose, check the scope output for an existing ELI5 page and point to it. If
  none covers the gap and a picture would help, build one with that skill.
- **Reasoning slips go to `reasoning-moves`**: correlation read as cause, a
  sample treated as a population, an assumption treated as fact.
- **Evidence, not vibes.** Status comes only from logged attempts. A completed
  kit, a confident tone, or one right answer is not competency.

## Content boundary

- Ask only about concepts in the scoped sections' Core notes and ledger
  **Earned** lists. Skip anything under **Uncertain** or **Not earned**
  (for example, boxplots if the source stopped before them).
- Scenarios may come from anywhere, but they add no new course facts. Label
  outside context as context.
- Never name where an idea was taught (deck, slide, figure, page). Ask about
  the idea itself (chapter-study-kit Practice rule 9).
- Never answer a graded quiz, exam, or discussion prompt. If the learner
  pastes one, switch to coaching: requirements, the concepts it tests, and a
  check of *their* draft.

## Start a session

1. **Resolve the scope.** Course and chapter range from the request; if either
   is missing, ask once. Then run:

   ```sh
   python3 "$SKILL_DIR/scripts/competency.py" scope --kit "<term>/<COURSE>/Chapter-Kits" --chapters 1-3
   ```

   It lists each section's concepts (numbered Core headings) with a status of
   `unassessed`, `fragile`, `developing`, or `secure`, the next review due,
   and the ELI5 pages that cover the section.
2. **Read before asking.** For each section in scope, read the Core notes and
   the ledger's Earned list. Read `Practice.md` too, so loop questions don't
   duplicate its items.
3. **Know the learner's field.** Use it from memory or earlier in the
   conversation; otherwise ask once ("What's your major or the field you
   want examples from?"). Scenarios come from that field first.
4. **Pick a mode.** **Live loop** (default) runs in chat. **Exam mode** runs
   when the learner asks for a test to take on paper or a tablet.

## Live loop

Read [references/lenses.md](references/lenses.md) before the first question.

1. **Sweep.** One question per `unassessed` or `fragile` concept, due
   reviews first, interleaved across sections (never five in a row from one
   section). Use the sweep lenses from the reference. Keep a round to about
   6–8 questions; ask whether to continue after each round.
2. **One question at a time.** Scenario, one question, wait. The learner may
   answer in chat or upload handwritten work; read images in place.
3. **Grade and log** each answer right away, using the grading table in the
   reference:

   ```sh
   python3 "$SKILL_DIR/scripts/competency.py" log --section "<section dir>" \
     --item "Core 5 · read the result" --result partial \
     --reason "right s, but called it the average distance in ms²" \
     --next "2026-09-30, Core 5 · anatomy"
   ```

   `Item` is `Core N · lens`. `Next review` names a date and a *different*
   lens for the same concept. Use 1 day after a miss, 3 after a partial or a
   first correct, 7 after a second correct.
4. **On `partial` or `missed`:** name what's right, the first thing that went
   wrong, and the fix in a sentence or two. Offer the ELI5 page if one covers
   it. If it's still shaky, hand the concept to `teach-complex-concepts` for
   a short teaching turn, then re-check with a new lens and a new scenario.
5. **Deepen.** For `developing` concepts, use the depth lenses (why it
   matters, anatomy, stress test, contrast). Save **teach-back** for concepts
   that are close to secure.
6. **Close the round** with a short summary: what's secure, what's fragile,
   the single weakest concept, and when each is due next. Don't restate every
   question.

## Exam mode

1. **Blueprint.** Weight the exam toward `fragile` and `unassessed` concepts,
   and toward **compute + read the result** for formula concepts. Mix raw-data
   and summary-table problems when the course uses both. List excluded topics
   (Uncertain or Not earned) on the exam page.
2. **Compute the key first.** Recompute every number in Python before writing
   the exam. Invented data is fine; wrong answers are not.
3. **Write two files** in that course's `Week-XX_*/Work/` for the current
   week: the exam page (`<course>-ch<A>-<B>-practice-exam.html`) and the key
   (`…-KEY.md`, opening with a do-not-open-until-graded warning, including
   partial-credit notes). Add an exam line to that Work README. Offer a private
   Artifact link for tablet viewing.
4. **Grade uploads** against the key: per item, the points earned, what's
   right, the first error, and the fix. Then log each item under its Core
   concept (`Core N · exam`) and use the misses as the next live loop's
   targets.

## Status rules

`competency.py` derives status from the log, mirroring chapter-study-kit's
three-session check:

| Status | Meaning |
| --- | --- |
| `unassessed` | no attempts logged |
| `fragile` | the latest attempt was partial or missed |
| `developing` | the latest attempt was correct, but not yet secure |
| `secure` | the last three attempts were correct, on three separate dates, with at least two different lenses |

Say "secure" only when the script says so. A secure concept still gets an
occasional check; its streak lowers its priority but doesn't exempt it.

## Done

- Every attempt in the session is logged, with a next review that uses a
  different lens.
- The learner knows their weakest concept and when it's due next.
- No graded work was answered, and no question named a slide, deck, or page.
