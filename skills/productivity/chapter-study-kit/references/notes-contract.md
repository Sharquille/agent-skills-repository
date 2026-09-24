# Notes contract

One canonical `*Study-Notes.md` per section on disk. GoodNotes receives **Core
only**. Self-test is Obsidian `Practice.md`, not a GoodNotes notebook.

Read [overwhelm-scaffold.md](overwhelm-scaffold.md) first.
For a source-based question count and the Practice quality check, read
[practice-planning.md](practice-planning.md).

## Shape

1. Map names the ideas. Notes do not reprint the map in prose.
2. Numbered sections. One idea per heading. When the lecture lists module or
   section objectives, that list is the Core spine: one heading per earned
   objective. Do not collapse a full slide module into a ten-heading recap.
3. Core: 1–3 short sentences, then a **TEST MOVE** line. That is the shape of
   one heading, not a word-count ceiling for the kit. When the source teaches
   a list (four cleaning mistakes, five shop steps, Fig 2-20), put it in a
   table. When compression loses the reason, add optional depth or a tiny
   worked example, still under that heading.
   For a procedure the source actually demonstrates, include one correct worked
   example with the decision points visible. Practice then fades one meaningful
   step before asking for independent near-transfer. Do not invent a procedure
   from a name-only objective.
4. Contrast as a real table (3+ rows × 2+ attributes) or a bold bullet pair.
   Required when the pages teach a pair: SRS vs “each person equal”;
   stratified vs cluster; observational vs experiment; lurking vs confounding;
   application vs system software; RAM vs ROM vs storage.
5. Group long Core with level-2 source sections (`## Section A`, `## 1.1
   Variable type`) and keep idea headings at level-3 so the 414 split follows
   the module. An objective with no body on the slides stays Uncertain; do
   not invent the missing procedure.
6. Worked stems kept **verbatim** only if the page printed them, then Official /
   Why / If you missed it. That block is **Quiz why** in the canonical file. Do
   not import it into GoodNotes.
7. Traps only from these pages.
8. Student self-test is `$SECTION/Practice.md`. Folded Obsidian callouts, one
   primary earned outcome each, full prompt in the title, answer hidden until tap:

   ```markdown
   > [!question]- Q01. Prompt in new wording of one earned idea?
   > **Answer:** Decision. **Why:** Source-based reason. **Review:** Core topic.
   ```

   Title the file for the section topic. New wording / transfer only. Never
   Official, never a quoted book stem, never homework numbers. Size the bank
   from earned atomic outcomes and documented confusions, not a fixed callout
   cap. Group a large bank into short rounds. Keep answers concise but complete.
9. Day 1 / 3 / 7 restudy `Practice.md` after the first actual study attempt,
   not after file creation. A miss routes back to the relevant Core heading,
   then a different item later; a miss on an `unverified` outcome routes to a
   source recheck instead. Record actual attempts only when supplied.
10. Canonical `*Study-Notes.md` callouts: `> [!NOTE]` / `TIP` / `IMPORTANT` /
    `WARNING` / `CAUTION` only. `Practice.md` may use `[!question]-`.

On first contact, Map → Core → Practice. On return, require a closed-book answer
or map reconstruction before using Map/Core as feedback. Adapt cueing from the
learner's recorded attempts and fade help after success; do not select formats
from learning-style labels.

Prose: unslop. No decorative emoji. No invented later-chapter traps.

## Editorial review before release

Read each Core heading and Practice item aloud in its source context. Rewrite
fragments as complete, plain-English explanations, with one test decision and
the reason behind it. Keep the lecture's objective spine, numbered headings,
revealed official answers, units, and source locators. Treat old prices and
platform tables as figures from the textbook's period. When source slides
contradict an authoritative technical source, verify the correction, record it
in the ledger, and show a short note at the affected Core topic. Do not invent
material for missing pages or objectives. Compare old and revised heading
numbers and coverage before regenerating the hub. A passed HTTP request cannot
replace an actual readability check in GoodNotes or a folded-answer tap in
Obsidian Reading view.

## Surfaces

| Surface | What lives there |
| --- | --- |
| GoodNotes **Map/** | Concept map + extra legend flows (levels, methods, pitfalls, tools) |
| GoodNotes **Notes/** | Core import only |
| GoodNotes **Retrieval/** | TD sort maps only (`*-decision-flow.mmd`, `*-error-flow.mmd`) |
| Obsidian `Practice.md` | Tap-to-reveal transfer items |
| Canonical `*Study-Notes.md` | Core + Quiz why (if printed) + author restudy pointer |

Do not put Quiz why or Retrieval prose notebooks in GoodNotes.

## 414 split

The builder derives GoodNotes markdown from **Core only**: text before the first
level-1 heading whose title contains `Quiz why` or `Retrieval`. Use level-2
headings for source sections so a long Core splits A–E (or 1.1 topics), not
mid-table. Keep idea headings at level-3. Official stems, tables, and code
fences stay together. Do not separately maintain Core/Quiz/Retrieval copies as
the source of truth. Maps stay one `.mmd` each. `Practice.md` is never a claim
URL.

Old Core/Quiz/Retrieval files are fallback inputs only when no canonical notes
exist. The GoodNotes fallback still sends **Core only**.

## Integrity

Textbook items with printed answers: explain why in Quiz why on disk. That is
study. Do not turn those stems into Practice.md items.

No printed answer: Practice.md with *new wording*, not a homework key.

Graded assignment screenshots: teach the method on different numbers. Do not
compute his data. Do not fill his table.

## Understanding and transfer

Coverage is what the sources supplied. Understanding is what the student has
shown. Never infer mastery from a completed kit or a correct copied answer.
Practice.md is the transfer check. Optional depth may explain earned concepts
but must not introduce later chapter material. Keep unsupported homework
"bridge tools" separate from the earned overall map.

Record optional results in `study-log.md`: attempt date, prompt ID, result
(correct/partial/missed), the student's reason, and the next review. No invented
scores or dates; a blank log is acceptable. Do not start reminders automatically.

```markdown
| Date | Item | Result | Reason given | Next review |
| --- | --- | --- | --- | --- |
| 2026-09-24 | Q03 | missed | Mixed up range and spread | 2026-09-26, Q06 |
```

Add a row only after an actual attempt. `Result` is `correct`, `partial`, or
`missed`; `Next review` names the date and a different item for the same outcome.
