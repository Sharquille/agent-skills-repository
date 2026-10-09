# Notes contract

One canonical `*Study-Notes.md` per section on disk. The GoodNotes notebook PDF
prints **Core only**. Self-test is Obsidian `Practice.md`, not the notebook.

Read [overwhelm-scaffold.md](overwhelm-scaffold.md) first.
For a source-based question count and the Practice quality check, read
[practice-planning.md](practice-planning.md).

## Shape

1. Map names the ideas. Notes do not reprint the map in prose.
2. Numbered sections. One idea per heading. When the lecture lists module or
   section objectives, that list is the Core spine: one heading per earned
   objective. Do not collapse a full slide module into a ten-heading recap.
3. Core: each heading follows the explanation order below, then a **TEST
   MOVE** line. Core prints Tier 1 items and what they depend on
   ([Relevance first](#relevance-first)), each fact once
   ([Say it once](#say-it-once)). Keep a heading short by splitting a long idea into smaller
   headings, never by skipping a step or a definition. When the source teaches
   a list (four cleaning mistakes, five shop steps, Fig 2-20), put it in a
   table.
   For a procedure the source actually demonstrates, include one correct worked
   example with the decision points visible. Practice then fades one meaningful
   step before asking for independent near-transfer. Do not invent a procedure
   from a name-only objective.
4. Contrast as a real table (3+ rows × 2+ attributes) or a bold bullet pair.
   Required when the pages teach a pair: SRS vs “each person equal”;
   stratified vs cluster; observational vs experiment; lurking vs confounding;
   application vs system software; RAM vs ROM vs storage.
5. Group long Core with level-2 source sections (`## Section A`, `## 1.1
   Variable type`) and keep idea headings at level-3 so the notebook pages follow
   the module. An objective with no body on the slides stays Uncertain; do
   not invent the missing procedure.
6. Worked stems kept **verbatim** only if the page printed them, then Official /
   Why / If you missed it. That block is **Quiz why** in the canonical file. It
   never goes in the GoodNotes notebook.
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
    `WARNING` / `CAUTION` only. A `TIP` whose body starts with `**SKETCH:**` or
    `**RECALL:**` is a margin prompt; one that starts with `**TERMS:**` is a
    margin glossary. An `IMPORTANT` that starts with `**HIGH YIELD:**` is a
    relevance highlight; a `NOTE` that starts with `**CURRENT EXAM (Wnnn):**`
    is a cited web addition (non-Monroe kits only). `Practice.md` may use `[!question]-`.
11. Figures are `.svg` files beside the notes, embedded with a Markdown image
    line; rules in [visual-language.md](visual-language.md#figures-in-core).

## Relevance first

An intro physics class teaches gravity without black holes. Core teaches what
the test asks and what that depends on, not every part of every part. The test
samples the objective list; it does not ask about every fact a source mentions.
Before writing Core, tag each earned ledger item with a tier in the ledger's
**Relevance** list:

| Tier | Decision rule | Where it goes |
| --- | --- | --- |
| 1 tested | Its term appears in an objective list mapped to this section (`objectives.md`, the lecture's objective list), or it decides an official quiz answer or a source-taught trap. The ledger names the matched objective line. | Its own Core heading: a visual or table when it has structure, a reason, a TEST MOVE |
| 2 supporting | Removing it leaves an undefined term or an unexplained step inside a Tier 1 explanation, or a plausible scenario question needs it to choose between two Tier 1 answers | One line or one margin TERMS entry inside the Tier 1 heading; no heading of its own |
| 3 context | Anything else the source mentions | The ledger's Context list only. It stays recoverable; Core does not print it |

- **Keep flows, cut fields.** A sequence (the client asks the AS for a TGT,
  the TGS issues a service ticket, the server accepts it) answers scenario
  questions, so it stays. An enumeration of fields, attribute examples,
  connection modes, or vendor names is Tier 3 unless an objective names it.
- **Both halves of a confusable pair stay** (two-step verification vs MFA,
  TOTP vs HOTP, FAR vs FRR): the test asks for the boundary.
- Depth follows the tier. A Tier 1 idea gets the visual, the reason, and the
  TEST MOVE; a Tier 2 idea gets one line. The heaviest Tier 1 headings carry a
  **HIGH YIELD** highlight with its reason
  ([relevance-research.md](relevance-research.md#in-the-notes)).
- With no objective list, the lecture checklist and official quiz decide Tier
  1; with neither, the source's headings, bold terms, and summaries do, and
  the ledger says so.
- Never cut a Tier 1 item to save space. Short notes come from cutting Tier 3
  and repeats.

## Say it once

Each fact appears once per heading, in the channel that carries it best:

- A figure or table carries structure, sequence, comparison, and lists. Prose
  does not restate what it shows. When a figure replaces a paragraph, delete
  the paragraph.
- Prose carries what a visual cannot: the reason, the exception, the decision.
  One caption line may state the inference a beginner would miss from the
  figure ("so the code never crosses a network"); a line that repeats a label
  does not.
- Use a visual wherever an idea has structure: a flow, a comparison, a
  hierarchy, a before/after. Plain definitions stay text.
- At most one reason line (**Why it works**, **Why it matters**, or
  **Builds on**), and only when it adds a cause the heading lacks. A bare
  dependency is a short tag: *Builds on 3.3 Core 16.*
- TEST MOVE is the scenario clue and the decision it points to. It never
  repeats a table row or a sentence above it; if it would, cut the sentence.
- Definitions live in the margin ([Margin definitions](#margin-definitions)).
  The body uses the term with no parenthetical expansion.

`validate_kit.py` warns when a heading carries more than one reason line.

## Margin definitions

Definitions go in the right writing margin, beside the heading that first uses
them, as a TERMS box placed right under the level-3 heading:

```markdown
### 6. Hard vs soft tokens

> [!TIP]
> **TERMS:**
> - **IdP**: identity provider; vouches for users to other organizations
> - **OTP**: one-time password; a code that works once
```

- Term or short form first, then its meaning in about twelve words or fewer.
- Include every official acronym (security kits) and every technical word a
  beginner would not know. Skip everyday ones (USB, URL) unless an objective
  list names them.
- At most six entries per box, so the margin keeps room to write. A heading
  that needs more is too big: split it.
- Define a term once per section. A later section repeats it in its own
  margin.
- The notebook prints the box in the margin; Obsidian shows it as a tip.

## Explanation order

Write every Core heading for a reader who has never seen the textbook:

1. **What it is**, in plain words. Every term and symbol is defined before its
   first use, in the margin or a Symbols table.
2. **Why it works**: the reason the rule or idea holds, from the source, when
   the text or figure does not already make it plain.
3. **What it builds on**: a short tag naming the earlier Core heading, when
   there is one.
4. **A worked example** when the topic involves a calculation (format below).
5. **TEST MOVE**: the clue in a question and the decision it points to.

Assume nothing about the vocabulary:

- **Codes and labels in words first.** Letter codes and labels (`BB`, `Bℓ`, `A`, `B`, `Q1`) are spelled out in words, in a small table when there are several, before the first example uses them.
- **Every technical word gets a short definition** in the margin where it first appears (dominant, genotype, mutually exclusive), even when the source assumes it.
- **Every formula gets three lines** right under it: **Read it aloud** (the formula as a plain sentence), **Use it when**, and **Don't use it when** (the case that calls for a different formula, by number).
- **A section with several formulas** opens with a **Which rule do I use?** table: the question's key word, the one deciding question, the formula, and what it does in plain words.
- When the slides print no numeric example for a formula, build one from earned numbers, label it derived, and check it a second way.

A section that uses notation (`P(A)`, `P(A | B)`, `Aᶜ`, `x-bar`, `σ`) starts
its Core with a **Symbols** table: symbol, how to read it aloud, and what it
means. Write math as `$...$` inline and `$$...$$` on its own line; Obsidian and
the notebook both typeset it (KaTeX). Use LaTeX commands (`\frac{1}{6}`,
`\mid`, `\cdot`), never a picture of an equation.

## Worked examples

A calculation is shown, not asserted. Use this exact layout so
`validate_kit.py` can trace it:

```markdown
**Worked example: A 5 on each of two dice**

**Situation:** The problem in one or two sentences (Example 4).

**Given:**

| Quantity | Value | Meaning |
| --- | --- | --- |
| Faces per die | 6 | each face equally likely |

**Steps:**

1. One die: $P(5) = \frac{1}{6}$, favorable faces over all faces.
2. Independent dice, formula (4): $\frac{1}{6} \cdot \frac{1}{6} = \frac{1}{36}$.

**Answer:** A full sentence with units or meaning.

**Check:** A sense check, such as a probability between 0 and 1.
```

- **Given** lists every number the problem states and what it means.
- Each **Step** does one calculation and says what it does and why. Numbers
  left of `=` must already be given or produced by an earlier step; numbers
  after `=` are what the step produces. 0, 1, 2, and 100 need no source
  (bounds, halving, squaring, percent).
- A count is shown by listing or multiplying the outcomes, never just stated.
- The validator rejects a missing part, parts out of order, or a number with
  no source. It cannot judge whether a step is correct, so the editorial
  review still re-works every example.

Study paths (first contact vs closed-book return) and cueing live in
[overwhelm-scaffold.md](overwhelm-scaffold.md).

Prose: unslop. No decorative emoji. No invented later-chapter traps.

## Editorial review before release

Read the Core once as someone who has never seen the textbook: every symbol
defined before use, every number traceable, no step skipped. Read it again for
repeats: strike any sentence that restates a figure, a table, the margin, or
another sentence, and move any Tier 3 detail to the ledger. Then read each Core
heading and Practice item aloud in its source context. Rewrite
fragments as complete, plain-English explanations, with one test decision and
the reason behind it. Keep the lecture's objective spine, numbered headings,
revealed official answers, units, and source locators. Treat old prices and
platform tables as figures from the textbook's period. When source slides
contradict an authoritative technical source, verify the correction, record it
in the ledger, and show a short note at the affected Core topic. Do not invent
material for missing pages or objectives. Compare old and revised Tier 1
coverage before rebuilding the notebook; every cut item is in the ledger's
Context list. A passed render check cannot
replace an actual readability check in GoodNotes or a folded-answer tap in
Obsidian Reading view.

## Surfaces

| Surface | What lives there |
| --- | --- |
| Notebook **Map pages** | Concept map + extra legend flows (levels, methods, pitfalls, tools) |
| Notebook **Notes pages** | Core and its figures, with TERMS definitions and SKETCH/RECALL prompts in the writing margin |
| Notebook **Retrieval pages** | TD sort maps only (`*-decision-flow.mmd`, `*-error-flow.mmd`), each behind a blank redraw page unless the kit's `blank_pages` is `none` |
| Obsidian `Practice.md` | Tap-to-reveal transfer items |
| Canonical `*Study-Notes.md` | Core + Quiz why (if printed) + author restudy pointer |

## Core in the notebook

The notebook builder prints **Core only**: text before the first level-1
heading whose title contains `Quiz why` or `Retrieval`. Each level-2 source
section starts a new page, so a long Core reads A–E (or 1.1 topics). Keep idea
headings at level-3; tables and code fences are kept whole on a page. Do not
separately maintain Core/Quiz/Retrieval copies as the source of truth. Maps
stay one `.mmd` each. `Practice.md` never goes in the notebook.

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
