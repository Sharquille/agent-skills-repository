# Round board

One page per round. It is the "never lose a moment to teach" surface: right
after each answer, the learner sees the question, their answer mapped to the
correct one, and the reasoning, without switching back to chat.

## What a card shows, top to bottom

1. **Question, as asked**: the full scenario with its options or table, not a
   summary. The learner should never need the chat to remember what was asked.
2. **Your answer → correct answer**, part by part, with ✓ or ✗ per row. A
   blank or "I don't know" shows as —. The rows follow **what the question
   asked**: the first row states the direct answer to the question itself
   ("Which one uses chance?" → "only (b)"), then one row per asked part.
   Translate the learner's words into the question's terms (calling a plan
   "systematic" means they said it uses chance). Grade anything extra they
   volunteered in a separate row marked "Extra", so a ✓ on a side detail
   never reads as the answer to the question.
3. **Words used here**: every term the question or reasoning relies on,
   defined plainly (`terms=[("chance", "…"), …]`). Never lean on a word the
   card hasn't defined.
4. **How to get it**: the picture beside the reasoning.
5. **Remember**: one line.

The open question (or breakdown step) sits at the top as a dashed card, so the
learner can read it on the board and answer in chat. Progress tiles link to
each card; the newest answered card comes first. Re-checks waiting in the queue
show only as a count, never by name.

## Spec

Write the spec in the scratchpad. `round_board.py` puts eli5-explainer's SVG
helpers on the path.

```python
from eli5_page import svg, box, text, arrow

ROUND = dict(
    course="MA-235", scope="Chapters 1–3", date="2026-09-27", number=1, planned=8,
    queued=3,                                   # re-checks waiting; shown as a count only
    slug="ma235-ch1-3-2026-09-27-r1",           # fixed for the round
    current=dict(num="Q2 · step 1", meta="1.2 · breaking it down", ask="<p>…full question…</p>"),
    cards=[dict(
        section="1.2", concept="Naming a sampling method", lens="contrast",
        verdict="missed",                       # correct | partial | missed
        ask="<p>…the question exactly as asked…</p><ul><li>…options…</li></ul>",
        parts=[("Plan A", "", "stratified: some from every server", False), …],
        terms=[("chance", "a random process picks, not a person"), …],
        why="…the reasoning; <b> allowed…",
        remember="…one line…",
        svg=svg(...),                           # the picture of the reasoning
    )],
)
```

Append a card after each answer, update `current` to the next question, and
rebuild. The board is a local file in the week's Work folder; it opens offline.
Set `wide=True` on a card whose picture is wide (a whole taxonomy) so the
picture spans the card above the text instead of shrinking beside it.

## The picture

Draw the reason, not the question:

| Question kind | Picture |
| --- | --- |
| Classify or sort | eli5-explainer's `eli5_flow.tree`: the **whole family**, every member at its own leaf (including ones the question didn't use), the root idea at the trunk, and a labeled band around each real grouping. Don't simplify away a layer that teaches something: for sampling, **chance** → **no grouping** (simple random, systematic) and **grouping** (stratified, cluster), with **convenience** on the other side. Put the mechanism in each leaf. Use `wide=True`. |
| Formula or computation | the numbers laid out as the formula works: deviations, products, the division |
| Resistance or outliers | a dot plot before and after, with the measures marked |
| Contrast pair | two boxes, with the deciding feature named under each |

Recompute every number before drawing it. A card never shows a slide, deck, or
page locator.
