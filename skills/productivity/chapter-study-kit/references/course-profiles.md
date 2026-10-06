# Course profiles

Every course behaves differently, so each kit names its **profile** in `hub.json`
(`"profile": "quantitative"`). The profile decides what the Core notes must
carry, which figures earn their place, and what `validate_kit.py` checks. The
shared rules (explanation order, worked-example trace, margin prompts, source
grounding) apply to every profile; this file adds what differs.

Pick the profile by how the course is tested, not by its department:

| Profile | Tested by | Kits now |
| --- | --- | --- |
| `quantitative` | calculating, reading formulas and graphs | MA-235 Statistics |
| `technical` | naming parts, protocols, and steps in a system | IT-100 |
| `security` | technical, plus choosing controls, policies, and responses against an exam objective list | CompTIA Security+ |
| `general` | explaining, interpreting, and arguing | EN-221, LA-122 |

Courses can overlap. Security is technical with governance on top, so a
`security` kit does everything a `technical` kit does. A technical course with
real calculations still writes traced worked examples for them.

## quantitative

- Open each notation-heavy section with a **Symbols** table; math is `$...$`.
- Every calculation the source prints becomes a traced worked example
  (Situation / Given / Steps / Answer / Check). A formula with no printed
  example gets a labelled derived one built from earned numbers.
- Every formula gets **Read it aloud / Use it when / Don't use it when**; a
  section with several formulas opens with a **Which rule do I use?** table.
- Figures: number lines, distributions and their shapes, sample-inside-population
  sets, grids of outcomes, tables turned into pictures that keep every cell.
- Practice: calculation answers show numbered steps.

## technical

- Open each section with an **Abbreviations** table: short form, what it stands
  for, what it means, and the Core heading that teaches it. Take expansions
  from the sources; when a source only uses the short form, give the standard
  expansion and keep the meaning tied to the notes.
- Every heading gets a **Why it works / Why it matters** or **Builds on** line
  that links it to the idea it depends on, so the section reads as a system.
- Figures: data flows and request/response paths, layered stacks, component
  diagrams (input → process → output), timelines of packets or events,
  before/after state (what survives a power-off).
- Worked examples only where the source prints numbers; do not invent speeds,
  prices, or sizes to manufacture one.

## security

Everything in `technical`, plus:

- **Exam objectives are the coverage spine.** The kit keeps `objectives.md`:
  one row per tested objective item mapped to Chapters on hand, with its
  status. A term in the objective list is a tested glossary entry: it must be
  defined in the section the objectives assign it to, or the row says where it
  is covered or that a later module owns it. An item a supplied source teaches
  but the notes skip is a gap to fill from that source, never from memory.
- **The official acronym list is the glossary.** The kit keeps `acronyms.md`,
  built from the exam objectives PDF with `scripts/acronym_map.py --kit
  <Chapter-Kits> --from-json <pairs.json>` (rerun without `--from-json` after a
  rewrite to refresh **Where**). Every official acronym a section's Core uses
  gets a row in that section's Abbreviations table, spelled out as the list
  spells it.
- **No scratch pages.** The notebook keeps the Retrieval redraw pages but drops
  the blank Scratch pads; answers go in the margin and `Practice.md`.
- **Visuals carry the relationships**, because policy-heavy material is easy
  to read and hard to keep:
  - comparison matrices (control category × control type, model × who decides)
  - attack and response chains (vector → exploit → impact → control that
    breaks the chain)
  - trust and key flows (who holds which key, what a certificate vouches for)
  - hierarchies (policy → standard → procedure → control) and zones
    (control plane vs data plane, inside vs outside a boundary)
  - one-picture decision sorts for "which control / which protocol fits"
- **Read the scenario, name the control.** Each idea's TEST MOVE says what clue
  in a question points to it, because the exam asks "given a scenario."
- Keep corrections the ledger records (a source conflict, an outdated claim)
  visible at the affected heading; a figure must not contradict them.
- **Guard against drift.** When rewriting, keep every existing Core sentence's
  meaning, heading number, figure, and Practice item unless the ledger shows it
  wrong; compare old and new Core before rebuilding.

## general

- Define every literary or discipline term where it first appears (dominant
  is to genetics what irony is to literature: a word the reader may not know).
- Figures only for structure: arcs, gaps, trees of types, process models,
  scales of distance or time. Most argument and definition stays text.
- Margin prompts ask for the concept, never a worksheet or graded answer.

## Checks by profile

`validate_kit.py --kit` reads the profile and adds these to the shared
contract. Warnings name what to add; errors block the notebook build.

| Check | quantitative | technical | security | general |
| --- | --- | --- | --- | --- |
| `hub.json` names a known profile | error | error | error | error |
| Every idea heading has a why / builds-on / read-aloud line | warning | warning | warning | warning |
| Section opens with **Symbols** when Core has math | warning | | | |
| Section opens with **Abbreviations** | | warning | warning | |
| `objectives.md` exists and every row is well formed | | | error | |
| Official acronyms the Core uses have an Abbreviations row; `acronyms.md` is current | | | warning | |
| A figure label prints at 8 or larger | warning | warning | warning | warning |
