# Code bootcamp variant (M LAB)

The second engine in this skill. Use it when the learner wants to **write,
debug and review code** in a language or tool the page can't run (Power
Query M, DAX, SQL against a real database, Excel formulas). The interview
engine is for speaking; this one is for building.

```text
ENGINE=$SKILL_DIR/assets/code-bootcamp       # engine.js, styles.css, shell.html, build.py, validate.js, briefs/common.txt
EXAMPLE=$ENGINE/example                      # M LAB's content.js, ref.js, modules/ (local only, git-ignored)
```

## What the learner gets

| Section | What it does |
|---|---|
| Command Center | Level and XP, project readiness, competencies by tier, weak areas, achievements, what to do next |
| Diagnostic | One question per area. It recommends a path and never marks anything mastered |
| Modules | Lessons with a short brief (concept, mental model, input → output contracts, syntax, a VBA-style comparison) and then practice: worked example, failure case, checkpoint. **Prove it** skips a lesson the learner already knows |
| Playground | Every example is editable and highlighted, with a copy button for the real tool |
| Challenge Arena | Predict the output, complete the expression, debug, refactor, catch silent corruption, review AI-written code, plus a timed boss |
| Review | Spaced repetition: a miss comes back tomorrow, clean answers wait 1, 2, 4, 7, 14, then 30 days |
| Lab Center | One lab per module, verified by pasting the real tool's output back, then scored by Claude on a weighted rubric |
| Reference | Searchable functions (purpose, syntax, parameters, returns, example, mistakes, use in the project, docs link), patterns, common errors, and a Tier 3 list |
| Capstone | A synthetic data pack with copy buttons, query briefs, exact output checks, a whole-solution review and a design defence |

## Rules this variant adds

1. **Never fake execution.** The page says plainly that it can't run the
   code. Every example copies straight into the real tool. Expected results
   are labelled "expected, not executed".
2. **Verification is real output.** The learner pastes the tool's result;
   `compareOutput` checks it cell by cell (column count, numbers with a
   decimal point or comma and no grouping, dates formatted yyyy-mm-dd). A
   check is tied to the code it was run with; editing the code clears it.
3. **Tiers decide depth.** Tier 1 is mastery (3+ attempts averaging 85%),
   Tier 2 is working knowledge (2+ at 70%), Tier 3 is reference only with no
   lessons. Readiness weights Tier 1 fully and Tier 2 by half.
4. **About 15% theory, 85% applied.** The brief is short; the VBA-style
   comparison and deeper notes are folded away.
5. **Contracts first.** Every lesson states each function's input → output,
   including what happens with null and errors.
6. **Mastery is earned.** Hints count 70%, a revealed answer counts 0, and a
   revealed lab solution blocks mastery. Labs need 85% on the rubric with no
   critical data-integrity failure and no failed output check.
7. **Grade ideas, not words** (same as the interview engine). The lab
   grader judges whether the approach and reasoning are sound; jargon and
   length earn nothing. Spoken explanations are read generously.
8. **All data is synthetic** and never presented as a real vendor
   specification.
9. **Display code exactly as typed.** No font ligatures (`=>` must not turn
   into an arrow). An option that is all code uses the code font; a sentence
   stays in the text font with its code pieces marked inline.

## Workflow

1. **Scope.** The subject, the real project it serves, the tool the learner
   runs code in, workplace constraints, and the module list with tiers.
2. **Copy the engine** into a new folder under `~/local-apps`. Fill the
   `[Project]`, `[processor]` and learner-English placeholders and the
   localStorage key in `engine.js`.
3. **Write `content.js`** (TIERS, COMPS, DIAG, EX, GEN, MODULES 1–2 by hand
   as the style model, LABS, ARENA, PATTERNS, ERRORS, CAPSTONE). Have Codex
   draft `ref.js`; check the risky entries yourself.
4. **Draft the remaining modules in parallel.** Each module is its own
   `modules/modN.js` calling `REG(N, {...})`. Write `briefs/common.txt`
   (format and accuracy rules) and one `briefs/modN.txt` per module with its
   topics, tiers and lab. Run one Sol agent per module:

   ```text
   orchestra-agent.sh consult --model sol --reasoning medium --cd . -- "$(cat briefs/common.txt) $(cat briefs/modN.txt)" > draft-modN.js
   ```

5. **Validate** each draft: `node validate.js modules/mod*.js` checks
   lessons, exercises (one correct option, reasons on every option), labs and
   ID clashes.
6. **Sol reviews accuracy** in pairs of modules at high reasoning, then the
   capstone's expected outputs are recomputed independently. Apply what
   holds; when a rule and the reference solution disagree, make the rule
   match the solution and say so.
7. **Self-test** (`#selftest`), then sweep every page for stray `null`,
   `undefined` or overflow at desktop and phone width.
8. **Publish** with capabilities `{db: {}, user: {}, sample: {}, downloads:
   true, dictation: {}, tts: {}}`.

## Errors

| Symptom | Fix |
|---|---|
| The word "null" appears on the page | Keep the append/replaceChildren patch at the top of `engine.js` |
| A lab passes in Excel but the check fails | Dates must be yyyy-mm-dd; numbers need no thousands separators |
| A draft module silently overwrites another's exercises | Run `validate.js`; prefix ids `mN-`, `lN-`, `aN-` |
| A syntax sample won't parse when copied | Every copyable block must be a whole `let … in` expression |
