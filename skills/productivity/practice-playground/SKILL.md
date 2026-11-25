---
name: practice-playground
description: "Build a great practice lab for any subject as one published Artifact, from two proven engines. Speak mode (Card Desk) drills interviews, oral exams and presentations: plain foundations, checks, answer builder, answering out loud with voice, a mock panel with AI scoring and the learner's own cue cards. Build mode (M LAB) teaches a language or data tool the page can't run, such as Power Query M, DAX, SQL or Excel formulas: tiered lessons with input → output contracts, labs verified by pasting the real tool's output and graded on a rubric, a challenge arena, a reference and a capstone. Both share spaced review, earned mastery, ideas-not-words grading, parallel agent drafting, a validator, Sol review and a self-test. Use when the learner wants a lab, playground, bootcamp, drill app, interview or exam prep, or anything like Card Desk or M LAB. Do not use for chapter notes or GoodNotes kits (chapter-study-kit), conversational quizzing (chapter-competency-loop), one-topic picture explainers (eli5-explainer), or graded coursework (assignment-workspace)."
# --- provenance ---
category: productivity
source: self-authored (this repository), extracted from the Card Desk playground and the M LAB bootcamp built in November 2026
author: Sharquille Andrew
license: MIT
retrieved: 2026-11-22
---

# Practice playground

One subject becomes one published Artifact that the learner drills daily.
The engines are proven; each new lab is mostly new content data.

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/practice-playground
SPEAK=$SKILL_DIR/assets/reference        # Card Desk engine; content.js is local only
BUILD=$SKILL_DIR/assets/code-bootcamp    # M LAB engine, validator, brief template; example/ is local only
```

## 1. Pick the mode

| The learner needs to… | Mode | Engine | Read before writing |
|---|---|---|---|
| Say answers well: interview, oral exam, presentation, viva | **Speak** | `$SPEAK` | `references/content-schema.md` |
| Write, debug and review work in a tool the page can't run | **Build** | `$BUILD` | `references/code-bootcamp.md` |
| Know a body of facts and judgement (certification, policy, product knowledge) | **Build**, without labs | `$BUILD` | `references/code-bootcamp.md` |

If a subject needs both (a technical interview), build in Build mode and add
the Speak engine's mock panel only if the learner asks for it.

## 2. Rules every lab keeps

These came from the learner's corrections. Do not drop them.

1. **Plain words, no fat.** Cut, don't hide. One idea once. Define a label
   before using it. Spoken model answers stay at 60 to 80 words.
2. **About 15% theory, 85% practice.** A short brief, then examples, checks,
   failure cases and labs. Deeper notes and comparisons fold away.
3. **Tiers decide depth.** Tier 1 is mastery, Tier 2 working knowledge,
   Tier 3 reference only with no lessons. Don't give every topic equal time.
4. **Let them skip what they know.** A diagnostic recommends a path; a
   "Prove it" or test-out lets them skip a lesson or module by demonstrating
   it. Skipping never creates a gap: the lab still has to be passed.
5. **Teach before test.** Every option carries a reason. Feedback teaches.
6. **Mastery is earned.** Hints count 70%, a revealed answer counts 0, and a
   revealed lab solution blocks mastery. Opening a lesson earns nothing.
7. **Grade ideas, not words.** AI scoring judges whether the approach is
   sound and fits the question. Model answers are one good answer, not a
   checklist. Jargon and length earn nothing; a short, plain, correct answer
   can score full marks.
8. **Speech is generous.** Dictation reads terms loosely and never marks
   accent, dialect or grammar. Default voice: Airy.
9. **Facts stay true.** The learner's own facts go in `[brackets]` until
   they supply them. Training data is synthetic and never presented as a
   real vendor or employer specification.
10. **Never fake execution.** If the page can't run the work, say so. The
    learner runs it in the real tool and pastes the output back for an exact
    check.
11. **Show code exactly as typed.** No font ligatures; prose stays in the
    text font with code pieces marked inline.
12. **Stay in scope.** Build what was asked. No optional extras.

## 3. Build it

1. **Scope.** Subject, purpose (event and date, or the real project it
   serves), the tool the learner works in, constraints, and the topic list
   with tiers. Gather the learner's real facts.
2. **Copy the engine** into a new folder under `~/local-apps`. Fill every
   `[bracketed]` placeholder in `engine.js` and `shell.html` and set a new
   localStorage key.
3. **Write the first one or two units by hand.** They are the style model
   every later unit copies.
4. **Draft the rest in parallel.** Write a shared brief (format, accuracy
   rules, style; start from `$BUILD/briefs/common.txt`) and one short brief
   per unit. Run one Sol agent per unit in the background:

   ```text
   orchestra-agent.sh consult --model sol --reasoning medium --cd . -- "$(cat briefs/common.txt) $(cat briefs/unitN.txt)" > draft-unitN.js
   ```

   Use Codex for bulk reference drafting. Keep judgement and integration
   yourself.
5. **Validate** every draft (`node validate.js modules/*.js` in Build mode):
   one correct option per question, a reason on every option, complete labs,
   no ID clashes.
6. **Sol reviews accuracy** at high reasoning, two units per review, plus an
   independent recomputation of any expected outputs. Apply what holds. When
   a stated rule and the reference solution disagree, make them agree and
   say which way.
7. **Self-test and sweep.** Serve `dist/`, open `#selftest` (title must read
   `selftest N/N`), then visit every page at desktop and phone width for
   overflow and stray `null` or `undefined` text. Stop the server after.
8. **Publish.** The first publish declares `{db: {}, user: {}, sample: {},
   downloads: true, dictation: {}, tts: {}}`; later publishes omit
   `capabilities` to keep them. Progress syncs through `db`.
9. **Reply.** What's in it, what Sol corrected, what isn't built yet, and
   any facts the learner still owes.

## Errors

| Symptom | Fix |
|---|---|
| The browser shows an old build | Add `?v=N` or reload |
| The word "null" shows on the page | Keep the append/replaceChildren patch at the top of `engine.js` |
| A pasted result fails although it's right | Dates must be yyyy-mm-dd; numbers need no thousands separators |
| Self-test fails "answer builder explains each beat" (Speak) | `BEAT_WHY[n]` length must equal `BEATS[n].beats` length |
| A unit restarts for the learner | Expected when its step count changes; say so in the reply |
| Drafts overwrite each other's exercises | Prefix IDs per unit; run the validator |
| A copied syntax sample won't run | Every copyable block must be complete code |
