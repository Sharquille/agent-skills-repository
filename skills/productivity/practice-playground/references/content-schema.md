# Content schema

`content.js` is plain data that the engine reads. The worked example is
`assets/reference/content.js` (Card Desk). Use `/* */` comments only.

## Paths

```js
const FOCUS = { delivery: "Project start to finish", you: "Your story" };   // tag labels

const UNITS = [
 { id: 1, focus: "delivery", title: "The morning alert", sub: "One-line promise", steps: [
   L("Lesson heading", `<p>…</p>`),        // a lesson, used in Full depth
   { t: "mc", … }, { t: "sort", … },        // checks (shapes below)
   { k: "cards", ch: 1 },                   // flashcards from BASE.cards for this path
 ] },
];
```

### Focus mode (the default)

```js
const FOUNDATION = { 1: `<div class="tablebox"><table class="plain">
  <tr><td><b>What it is</b></td><td>…</td></tr>
  <tr><td><b>When it comes up</b></td><td>…</td></tr>
  <tr><td><b>Why it matters</b></td><td>…</td></tr></table></div>
  <div class="callout"><b>They might ask:</b> “…” “…”</div>
  <div class="callout gold"><b>How to answer:</b> “…”</div>` };

const FOCUS_PLAN = { 1: ["u1-why-log", "u1-routine"] };   // 1 to 3 check ids per path
const SCENES = { 1: "One sentence that sets the moment." };  // shown above the foundation
```

A Focus path runs: foundation (with the scene line) → the checks in
`FOCUS_PLAN` → the answer builder → say it out loud → any `EXTRA_SAY`
questions.

### Answer builder and speaking

```js
const BEATS = { "1": { beats: ["First thing you say", "…"],          // the one correct order
                       extras: [["A wrong beat", "Why it doesn't belong"]] } };
const BEAT_WHY = { 1: ["Why beat 1 comes first", "…"] };   // same length as beats
const SAY_PTS  = { 1: ["Point a strong answer covers", "…"] };   // used for scoring
const SAY_MODEL = { 1: "Spoken model answer, 60 to 80 words, method first." };
const EXTRA_SAY = { 10: ["g14", "g17"] };   // more GENERAL_QS spoken at the end of a path
```

`BASE.say[n] = { q, a }` supplies each path's question (built by
`build.py`); `SAY_MODEL[n]` overrides the answer text.

## Check shapes

| Type | Fields | Notes |
|---|---|---|
| `mc` | `id, q, opts, why` | The correct option goes first; the engine shuffles |
| `sort` | `id, q, ctx?, buckets, items: [[text, bucketIndex, reason]], why` | Add `SORT_DEFS[id]`: one `[definition, clue]` per bucket |
| `order` | `id, q, steps, extras?, why` | Add `ORDER_WHY[id]`: one reason per step |
| `build` | `id, q, slots: [{ lab, opts }], why` | The correct option is first in each slot; add `BUILD_WHY[id]` |
| `num` | `id, gen` | A generated calculation; generators live in `engine.js` |

Every option needs a reason the learner can learn from. Exactly one answer
must be defensible: put the facts that decide it in `q` or `ctx`.

## Cases

```js
const CASES = [{ id: "tap", title: "…", kind: "Optional product", focus: ["delivery"],
  brief: "The situation in two sentences.",
  steps: [{ q: "Decision?", opts: [[text, 2, reason], [text, 1, reason], [text, 0, reason], [text, 0, reason]] }],
  wrap: "The method in one line.", say: "How to say the case answer in an interview." }];
const CASE_Q = { tap: "g1" };   // the interview question each case prepares
```

Four options per step, exactly one scored 2.

## Interview questions

```js
const GENERAL_QS = [{ id: "g1", who: "M", focus: "delivery", q: "…",
  pts: ["What a strong answer covers"], model: "Optional model answer",
  twin: "say4" /* optional: never asked together with say4 in one mock */ }];
```

`PANEL` in `engine.js` names the panelists (`M`, `HR`). `buildPlan()` picks
the mock set: an opener, one question per focus, any forced question, a
STAR story, and a close.

## Warm-ups

```js
const WARM_QS = [{ id: "open", who: "HR", warm: true, q: "Tell us about yourself.",
  pts: ["Who you are", "What you do now", "Your foundation", "Why this role"], model: "…" }];
```

The `open` warm-up starts every full mock. Warm-ups are coached and can be
kept like any answer, but never count toward mock averages or focus scores.

## Kept versions

Nothing to write: the engine stores `S.mine[questionId] = { text, at, rounds,
hist }` when the learner keeps a version. Cue cards and the grader use it.

## Writing rules

- Plain words. If a term must stay, define it the first time.
- Brackets for every fact only the learner knows: `[time before and after]`.
- One idea once across lesson, checks and answers.
- Model answers: method first, one example, 60 to 80 words.
