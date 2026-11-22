---
name: practice-playground
description: "Build a guided practice playground as one published Artifact: short paths (plain foundations lesson, two or three checks, an answer builder, then answering out loud with voice), branching scenario cases, a mock panel with AI scoring, and spaced review that stops the day before the event. Built from a proven engine (the Card Desk interview playground) by writing new content data, then self-tested in the browser, reviewed by Sol, and published. Use when the learner wants an interactive practice app, a playground like Card Desk, or interview, oral-exam, presentation or certification prep they can drill and speak through. Do not use for chapter notes or GoodNotes kits (chapter-study-kit), conversational quizzing (chapter-competency-loop), one-topic picture explainers (eli5-explainer), or graded coursework (assignment-workspace)."
# --- provenance ---
category: productivity
source: self-authored (this repository), extracted from the Card Desk playground built in November 2026
author: Sharquille Andrew
license: MIT
retrieved: 2026-11-22
---

# Practice playground

One event (an interview, an oral exam, a presentation) becomes one
published Artifact that the learner drills daily and speaks through. The
engine is fixed and proven. Each new playground is mostly new content data.

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/practice-playground
REF=$SKILL_DIR/assets/reference          # engine.js, shell.html, styles.css, build.py, content.js (Card Desk)
```

`content.js` holds the learner's own stories, so it is git-ignored and
exists only on this machine. If it is missing, work from
`references/content-schema.md`. The `[bracketed]` lines in `engine.js`
(`SPEECH_NOTE`, `Candidate background`, `ROLE`, `PANEL`, the event date and
the Today panel line) must be filled for each learner.

Read `references/content-schema.md` before you write content.

## What the learner gets

| Section | What it does |
|---|---|
| Today | Countdown, time left at the learner's own pace, and the next thing to do |
| Paths | One path per topic: foundations, then checks, then build the answer, then say it |
| Cases | Branching scenarios, four options per decision, scored 2/1/0 with reasons |
| Review | Spaced repetition of missed items: 1, 2, 4, 7 days, never past the day before the event |
| My answers | Every question with the learner's kept version: practise out loud, edit, or restore an earlier version |
| Mock | A panel asks a full set of questions; the learner speaks; Claude scores each point. Warm-ups (tell me about yourself and the like) are coached but never counted |

Two depths: **Focus** (default, about five steps per path) and **Full depth**
(every drill), toggled on the Paths page.

## The learning design (keep it)

These rules came from the learner's corrections. Do not drop them.

1. **Foundations first, plain words.** Each path opens with one lesson:
   What it is, When it comes up, Why it matters, They might ask, How to
   answer. No insider jargon. The learner must not sound like they already
   do the job.
2. **No fat.** Cut, don't hide. One idea once. No situation step, recap step
   or "where this is heading" step in Focus mode. Spoken model answers stay
   at 60 to 80 words.
3. **Teach before test.** Every check teaches with its feedback; every option
   has a reason. Define a label before you use it.
4. **Method first, example second** in every model answer.
5. **The learner's facts stay theirs.** Put anything you don't know in
   `[brackets]`. Never invent numbers, roles, approvers or results.
6. **Answer shapes for experience questions.** Learning something new: What
   I did, Who I asked, Who I helped. Project questions: actual, then
   hypothetical. A tool they built: Manual, Automated, then the deadline it
   checks.
7. **Speech is generous.** Dictation reads terms loosely and never grades
   accent or dialect. Default voice: Airy.
8. **Grade ideas, not words.** AI scoring judges whether the approach is
   sound and fits the question. Answer points and model answers are one good
   answer, not a word checklist. Never reward jargon; flag it when it stands
   in for a decision. A short, plain, correct answer can score 5. Keep this
   wording in `gradeItems()` and `getFollow()` in `engine.js`.
9. **The learner builds their own cue cards.** After each spoken round the
   feedback offers "Make it yours": start from what they said or the stronger
   version, keep the framing they like, edit, keep. The cue card then shows
   their version, the grader builds "better" on it, and the last 8 versions
   stay restorable (`S.mine`, merged across devices in `mergeState`).
10. **Stay in scope.** Build what was asked. No optional extras in the page
   or the reply.

## Workflow

1. **Scope.** Confirm the event, the date, who is on the panel, and the 8 to
   10 topics. Gather the learner's real facts and stories. Mark unknowns as
   `[brackets]`.
2. **Copy the engine.** Make a new folder for the playground (outside
   iCloud-synced folders when git is involved). Copy `shell.html`,
   `styles.css`, `engine.js` and `build.py` from `$REF`. Rename the brand,
   the localStorage `KEY`, the event date default and `PANEL` labels in
   `engine.js` and `shell.html`.
3. **Write `content.js`** to the schema: `UNITS`, `FOUNDATION`, `FOCUS_PLAN`,
   `BEATS` and `BEAT_WHY`, `SAY_PTS`, `SAY_MODEL`, `CASES`, `GENERAL_QS`,
   `WARM_QS`, `SCENES`. Use `$REF/content.js` as the worked example. Write all content
   in plain words first; add full-depth drills only if the learner wants
   them.
4. **Adapt `build.py`.** It inlines styles, content and engine into the
   shell. Replace the Card Desk story parsing with a small `BASE` object
   (say questions, recall blocks, follow-ups, opener) or drop it.
5. **Self-test.** Serve `dist/` and open `#selftest` in the built-in browser:

   ```bash
   cd <playground>/dist && python3 -m http.server 8813 --bind 127.0.0.1
   ```

   Open `http://127.0.0.1:8813/<file>.html?v=N#selftest`. The tab title must
   read `selftest N/N` with no FAIL lines. Add a check to `selfTest()` for
   each new rule. Garbled quotes on the local server are a charset quirk
   only. Stop the server and close the tab afterwards.
6. **Sol review.** Every build gets a read-only Sol review before publishing:

   ```text
   orchestra-agent.sh consult --model sol --reasoning high --cd . -- "<brief>"
   ```

   Ask for accuracy, plain language, one defensible answer per check,
   invented learner facts, and consistency between lesson, checks and model
   answers. Verify each finding, then apply the ones that hold.
7. **Publish.** Load `artifact-design` and `artifact-capabilities` first.
   First publish declares `{dictation: {}, sample: {}, tts: {}, db: {},
   user: {}}`. Later publishes omit `capabilities` to keep them. Progress
   syncs through `db`; a path whose step count changed restarts, finished
   paths stay finished.
8. **Reply.** Say what changed, what Sol corrected, and which `[bracket]`
   facts the learner still owes.

## Errors

| Symptom | Fix |
|---|---|
| Browser shows the old build | Add `?v=N` or reload |
| Self-test fails "answer builder explains each beat" | `BEAT_WHY[n]` length must equal `BEATS[n].beats` length |
| A path restarts for the learner | Expected when its step count changes; say so in the reply |
| `//` comment breaks an inlined line | Use `/* */` in content and engine |
