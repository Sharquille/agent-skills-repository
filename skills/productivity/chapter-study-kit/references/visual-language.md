# Visual language

Copy these `classDef` blocks. Do not invent a second palette.

```text
classDef root fill:#1F3A5F,stroke:#1F3A5F,color:#FFFFFF,font-weight:bold,font-size:18px
classDef intro fill:#EEF3F8,stroke:#8FA8BE,color:#24313F
classDef hubV fill:#EFE9FA,stroke:#9B8AB8,color:#3E3357,font-weight:bold
classDef leafV fill:#F8F4FD,stroke:#B9A9D1,color:#4A3D63
classDef hubD fill:#E7F4EC,stroke:#6FA98A,color:#2F4F3C,font-weight:bold
classDef leafD fill:#F3FAF6,stroke:#93C2A8,color:#37543F
classDef hubI fill:#FBEFE3,stroke:#C98F5A,color:#5C4023,font-weight:bold
classDef leafI fill:#FEF8F1,stroke:#DBAC7E,color:#654626
```

- Navy root = course or chapter title
- Intro gray = definition / remember / gather
- Purple = variable hub and leaves
- Green = descriptive / population / parameter
- Peach (`hubI` / `leafI`) = inferential, **only after that chapter is earned**

Node labels: `<br/>` for line breaks. Keep text short enough to read on iPad.

**One job per map.** The filename and the root node say that job. A taxonomy
root can be the module or section title; leaves answer the job. Do not put
shop, storage, and "what is a computer" on the same chart.

**Labels are the course’s words.** Take them from the ledger: OCR, lecture
objectives, inspected figures. Stats 1.1 (`Individual`, `Qualitative`,
`Appearance`) and Module 2 (`IPOS`, `stored program`, `Fig 2-20`) are the pattern. A quiz-sort
root may be a question the source asks. Do not invent quiz-show phrasing
(`Can it load a new program?`) that the notes do not use.

**LR** = `flowchart LR` (concept / taxonomy). **TD** = `flowchart TD` (quiz sort).

**Parallel fork:** independent ideas after a named hub both leave the same
parent; do not draw a taxonomy as a causal chain. 1.1 worked example (keep this
pattern): `VAR --> VT` and `VAR --> DS`. Ordered steps are a chain with one
exit. Lookup facts can hang off a step with a dotted edge so they do not look
like the next step.

## Figures in Core

Maps name the ideas; a Core figure shows how one idea works, right after the
text it illustrates. Every new section gets figures for the ideas that are
spatial, ordered, set-like, a contrast, a procedure, or a scale (population
inside sample, levels of measurement, sampling methods, frame and
undercoverage, selection then assignment). Skip ideas that are only a
definition or an argument in prose; a literature section may need none.

1. **One idea per figure, and the text stays.** A figure adds a picture of
   the mechanism; it never replaces the explanation or the TEST MOVE.
2. **Labels on the picture, in the course's words** from Core and the ledger.
   Numbers come only from the notes or ledger; `validate_kit.py` rejects a
   multi-digit, decimal, or percent value it cannot find there. Placeholders
   that only show a pattern (`Climber 1`, `here k = 4`) read as examples.
3. **Same meaning, same colour, in every figure:** green = population,
   parameter, descriptive; navy = sample, statistic; purple = individuals and
   variables; peach = inferential, traps, errors, undercoverage. Palette
   colours only; the validator rejects others.
4. **Replace a table only when the figure holds every cell** (the levels
   staircase, the sampling-method panels). Otherwise keep the table and draw
   the relation the table cannot show.
5. **No decoration and no caption that repeats nearby text.** A picture that
   does not carry the idea costs attention.
6. **Check the figure against its definition sentence.** A shape can teach the
   opposite of the words (undercoverage is only the population outside the
   frame, never inside it). Render the page and inspect it for overlap and
   clipping before release.
7. **One margin prompt per level-2 group**, drawn before looking at the figure:

   ```markdown
   > [!TIP]
   > **SKETCH:** The population circle with a sample inside. Tag P and S.
   ```

   Use `**RECALL:**` for a list to write from memory. The notebook prints it in
   the writing margin; Obsidian shows a tip callout.

Build figures with `scripts/svg_figure.py` (palette, labels, boxes, circles,
arrows, accessible `<svg>`), save each as `<prefix>-<section>-fig-<idea>.svg`
beside the notes, and embed it on its own line with alt text that states the
idea: `![Levels of measurement as a staircase](stats-1.1-fig-levels.svg)`.
Figures must have `role="img"` and an `aria-label`, and no scripts, links, or
embedded images.
