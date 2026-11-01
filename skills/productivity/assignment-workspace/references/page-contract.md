# Page contract

Every page is one self-contained `.html` file in the week's `Work/` folder.

## All pages

- CSP meta: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'`.
  No external fonts, scripts, or images.
- Color tokens on `:root`, a dark-mode override under
  `@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`,
  and an explicit `body` background.
- Works at phone width with a 16px side gutter and no horizontal scroll.
- A sticky top bar with section links and, on writing pages, a live total.
- `localStorage` keys are prefixed per assignment (`en221w8-`, `it100w6-`).
  Wrap every read and write in `try/catch`, so the page works without storage.
- Writing boxes use the submission font (Times New Roman for EN-221, Arial
  when the prompt says Arial) so length looks right.
- Name files `<COURSE>_Week<N>_<Kind>.html`, or follow the week's existing
  names.

## Workspace page (always)

1. Header: course, week, deadline with time zone, points, and SafeAssign if on.
2. **Requirements checklist** copied from the prompt (checkboxes that save).
3. **Plan:** for essays, paragraph roles with beats; for question sets, per
   question "What it asks", "Where to look" (¶ and page), "A strong answer",
   and a caution where a trap exists.
4. One `<textarea>` per paragraph or question, with a live counter that
   matches the prompt's limit: sentences per paragraph (green inside the
   range, amber outside), words per post, or total words for a one-page rule.
5. A reader link on every evidence question:
   `<a href="<Reader>.html#<question-id>" target="_blank">Open the reading at this spot, highlighted ↗</a>`.
6. **Works Cited** (MLA): entries in a hanging-indent block, a copy button,
   the in-text rules for each source, and a note to re-italicize container
   titles after pasting.
7. Copy-all, which joins the answers with question labels, plus a format
   section listing the Word or Docs steps.

## Discussion workspace

Prompt with guiding questions as checkboxes (cover 3–4, not all), angle cards
built from the learner's own semester work, a 3-paragraph shape, post boxes
with a word target (usually 250–300), and two reply boxes with the
three-step recipe: name a point, add something, ask a question.

## Reader

Built by `scripts/build_reader.py`; see `reader-spec.md`. Opens at
`#<question-id>`, spotlights the paragraphs, highlights phrases, has phrase
chips that jump, "PDF p." links at each page break, and click-to-copy
citation tags.

## Annotated scene (on request)

The scene from where it starts to the end, split into paragraph scraps.
Highlight and underline evidence, and use a second color for **gaps**: things
the original narrator didn't see or explain, which a new narrator can fill.
Put numbered notes under each scrap, tagged by the paragraph of the plan
they serve, with consistency guardrails (what the character would not do).
Add a few backstory scraps from earlier in the text for the intro.

## Model example (on request)

An invented story with no connection to any course text, then a model
answer in the assignment's exact shape, with a note under each paragraph
naming the requirement it meets and its sentence count. Every sentence is
complete, with no fragments. End with a side-by-side table that maps the
model's parts to the learner's assignment, and "copy the moves, not the
words."
