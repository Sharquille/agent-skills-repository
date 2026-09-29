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

0. **Housekeeping check first.** Before any question, settle where we are and
   what this is for, and keep it in the tracker (`<course>/competency-tracker.json`):

   ```sh
   python3 "$SKILL_DIR/scripts/competency.py" week --course "<term>/<COURSE>"
   python3 "$SKILL_DIR/scripts/competency.py" tracker show --course "<term>/<COURSE>"
   ```

   - **Current week:** from today's date and the week folders. New files
     (round board, exam, key) go in *this* week's `Work/`, not in the week a
     section was taught. The ELI5 explainers are the exception; they stay with
     their section's week.
   - **Goal:** why we're studying (an upcoming exam, a quiz, general review)
     and its date if there is one. Don't infer an exam from the chapter list;
     ask.
   - **Scope:** the chapters or sections in play.
   - Say what you inferred in two or three lines and ask the learner to
     confirm or correct it. Save it only after they answer:
     `competency.py tracker set --course … goal="Exam 1" goal_date=2026-10-01 chapters=1-3 week=4`.
   - On later sessions, show the saved tracker and ask only about what may
     have changed (a new week has started, the exam passed).
1. **Resolve the scope.** Course and chapter range from the request; if either
   is missing, ask once. Then run:

   ```sh
   python3 "$SKILL_DIR/scripts/competency.py" scope --kit "<term>/<COURSE>/Chapter-Kits" --chapters 1-3
   ```

   It opens with coverage by chapter (how many concepts are covered, and how
   many are still outstanding: bug hunt due, developing, fragile, or not yet
   checked). Covered concepts are listed once and drop out of the table. The
   rest show a status of `unassessed`, `fragile`, `developing`, or
   `bug hunt`, the **lenses tried** with their
   results, the **next check** that concept needs, the next review due, and
   the ELI5 pages that cover the section. Run it at the start of every
   session and before each round, and pick questions from it; the study logs
   are the record, not memory of an earlier chat.
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
   section). Queued twins (see Adaptive checks) slot in once their spacing is
   met. Use the sweep lenses from the reference. Keep a round to about
   6–8 questions; ask whether to continue after each round.
2. **One question at a time.** Scenario, one question, wait. The learner may
   answer in chat or upload handwritten work; read images in place.
3. **Grade and log** each answer right away, using the grading table in the
   reference. Before marking anything wrong, check the answer against every
   reasonable reading of the question; an answer right for the real-world
   reading is right.

   ```sh
   python3 "$SKILL_DIR/scripts/competency.py" log --section "<section dir>" \
     --item "Core 5 · read the result" --result partial \
     --reason "right s, but called it the average distance in ms²" \
     --next "2026-09-30, Core 5 · anatomy"
   ```

   `Item` is `Core N · lens`. `Next review` names a date and a *different*
   lens for the same concept. Use 1 day after a miss, 3 after a partial or a
   first correct, 7 after a second correct.

   `log` then prints the concept's status and syncs its re-check queue to
   the coverage flow (see Adaptive checks): twins while it's being learned, a
   bug hunt once competency is shown, nothing once it's covered. Pass
   `--answers <queue id>` when the question was a queued re-check, so it is
   closed. Put the same follow-up on the card as `next=`.
4. **Teach on every answer, right or wrong.** After grading, add a card to the
   round board: the question exactly as asked, the learner's answer mapped
   part by part to the correct answer, *how to get it* with a picture, and
   one line to remember. Put the next question (or breakdown step) at the top
   of the board so the learner can read it there and answer in chat. A
   correct answer still gets its card, because showing why it's right is what
   locks it in. See [references/round-board.md](references/round-board.md).
   The builder refuses a board whose ✓/✗ marks contradict a card's verdict
   or whose labels would be clipped. After it builds, look at the changed
   card once: every mark matches the row, only wrong answers are struck
   through, and the first row answers the question that was asked. A wrong
   mark on the board misleads exactly the learner who is unsure.

   ```sh
   python3 "$SKILL_DIR/scripts/round_board.py" "$SCRATCH/<round>.py" --work "<course>/Week-XX_*/Work" --course "<course>"
   ```

   The board is a local HTML file in the week's Work folder, so study
   material stays offline and outside any one app. Don't publish it as a
   hosted page unless the learner asks. Each build also saves the round's
   cards as JSON beside the board; that record, not the scratch spec, is
   what later sessions rebuild from (`round_board.py <record>.json`).

   With `--course`, every build then runs the **mastery sync**: cards whose
   topics (`cores=[...]`, Core numbers in the card's section) are all
   `covered` move off the round boards into
   `<course>/Mastery/chapter-NN-mastery.html`, grouped by section and topic.
   Their tiles link there. Everything still on a board is for review, and
   a topic that loses coverage goes back to its board. Run
   `mastery.py sync --course <course>` on its own after a log fix.
5. **On `partial` or `missed`:** name what's right, the first thing that went
   wrong, and the fix in a sentence or two. Offer the ELI5 page if one covers
   it. If it's still shaky, hand the concept to `teach-complex-concepts` for
   a short teaching turn, then re-check with a new lens and a new scenario.
6. **Follow the next check; never repeat.** Ask each concept what the
   scope's **next check** says. Once competency is shown, the concept gets a
   **bug hunt**, not another question like the one it passed. `covered`
   concepts are never asked again, so the outstanding list shrinks and the
   round moves on to other topics.
7. **Close the round** with a short summary: what's newly covered (and
   moved to its chapter mastery file), what's fragile, how many concepts are
   still outstanding per chapter, and the single weakest concept. Don't restate every
   question.

## Help menu

When the learner types `help`, show this menu (it's also printed on the round
board). Commands that change saved data (the tracker, `study-log.md` rows, or
file locations) are proposals: state the exact change and wait for a yes.

| Command | Does |
| --- | --- |
| `help` | show this menu |
| `status` | the tracker plus each concept's status |
| `set goal …` / `set exam date YYYY-MM-DD` / `set chapters 1-3` / `set week N` | change the tracker (confirm first) |
| `move files to week N` | move this round's files to that week's Work folder and fix the README lines (confirm first) |
| `hint` | the next step of the hint ladder for the open question |
| `explain` | stop and teach the concept now, then continue |
| `easier` / `harder` | change the next question's difficulty |
| `skip` | move the open question to the queue without scoring it |
| `fix log …` | correct a logged result (confirm first; never edit silently) |
| `end round` | close the round with its summary |

The re-check queue lives in the tracker. `log` keeps it in step (see Live
loop, step 3); run `queue tick` after each question asked and `queue due` to
see which re-checks have waited long enough. `queue sync` re-derives the whole
queue from the study logs; `queue add` and `queue done` are for manual fixes.

## Adaptive checks

One answer never finishes a concept: a correct answer is followed by a bug
hunt (see **Coverage flow** below), and a wrong one by **twins**: questions
with the *same decision logic and cues* in a *different scenario* (new
surface, new numbers, new wording).

| Answer | Read as | Next for that concept |
| --- | --- | --- |
| correct (confident or hedged) | competency shown | a **bug hunt** in a new scenario; a hedged answer is exactly what the bug hunt tests |
| partial | shaky | one twin at the **same** difficulty, then the bug hunt |
| missed, "no" / "idk", blank, or far off | weak area | **break it down** (below), then **two** twins in two different scenarios, then the bug hunt |

Confidence comes from the answer itself: hedges, question marks, "not sure,"
or a guess read as low confidence. Speed isn't visible in chat; if the learner
says they took a while or guessed, treat it as low confidence.

**Break it down.** Hand the concept to `teach-complex-concepts`: split the
decision into its smallest steps and have the learner do each one (its hint
ladder, worked step, then completion problem). Move on only when each step is
done unaided.

**Define before you rely.** List every term the explanation or a breakdown
step leans on ("chance," "group," "interval," "deviation") and define each in
plain words, from the kit's Core notes, before using it. If a step depends on
an idea the learner hasn't shown, check that idea first with a tiny step 0.
On the board, put these in the card's "Words used here" box.

**Two misses in a row on one concept, move on.** If a breakdown step also
gets "idk" or a blank, stop drilling that concept: show the step fully worked
on its card, keep its twins queued, and switch to a *different* concept. The
missed concept comes back from the queue once its spacing is met. Don't offer
to pause as the fix; switching concepts is the change of gears, and the
learner can still type `pause` or `end round`.

**Space the re-checks.** Queue every twin behind other questions: at least
**3** other questions later in the round, or at the start of the next round if
fewer than 3 remain. Never ask a twin right after its card. A twin never
reuses the card's numbers, wording, or picture, so it can't be answered from
what the learner just read.

**Coverage flow.** Every concept (a numbered Core topic) moves through three
stages, and `competency.py` enforces them from the log:

1. **Competency.** A correct answer shows it. After a partial, one correct
   twin is owed first; after a miss, two (breakdown steps teach but don't
   count). Hedged or not, a correct answer moves on, because the bug hunt
   tests it next.
2. **Bug hunt.** One question with a planted mistake in a claim, a
   calculation, or a classification: the learner finds it, fixes it, and says
   why. Pass it and the concept is **covered**. Miss it and **two** more bug
   hunts are owed, and both must be right. Miss both and the concept is no
   longer covered: **re-teach it** (card, ELI5 page, breakdown), then back
   to competency and a fresh bug hunt. One of the two right earns one final
   bug hunt: pass is covered, miss is re-teach.
3. **Covered.** The concept leaves the outstanding list and is never asked
   again; study continues with the other outstanding topics.

Log every attempt with its lens (for example `Core 7 · contrast twin`, and
`Core 7 · bug hunt` for the mastery check; only items named `bug hunt` count
as one).

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

`competency.py` derives status from the log with the coverage flow:

| Status | Meaning |
| --- | --- |
| `unassessed` | no attempts logged |
| `fragile` | still learning, with no correct twin since the last partial or miss (or re-teach due) |
| `developing` | still learning; some twins right, more owed |
| `bug hunt` | competency shown; a bug hunt is owed (1, 2, or a final one) |
| `covered` | passed its bug hunts; off the list, not asked again |

Say "covered" only when the script says so. Chapter-study-kit's own `secure`
check in the ledger is separate and unchanged.

## Done

- Every attempt in the session is logged, with a next review that uses a
  different lens.
- The learner knows their weakest concept and how many are still
  outstanding in each chapter.
- No graded work was answered, and no question named a slide, deck, or page.
