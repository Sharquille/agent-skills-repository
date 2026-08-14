---
name: visualize-study-chapter
description: "Turn an existing study chapter or section into a compact, interactive, visual-first study surface using the Visualize plugin. Use when a learner asks to visualize a chapter, make dense notes easier to digest, replace long scrolling with concept maps, flows, comparisons, trust boundaries, or timelines, or create one visual surface per chapter from material already present in an obsidian-study-loop vault. Scope-locks every visual to real source notes, protects active quiz and study-check evidence, and never changes mastery. Do not use to invent course content, grade the learner, make generic data charts, or create persistent Obsidian Canvas maps."
---

# Visualize Study Chapter

Turn one existing chapter into a visual study surface that lets the learner
select a section and see its relationships without rereading a long wall of
prose. Keep the source notes canonical. The visual is a temporary study aid,
not a second note system or an assessment.

## Coordinate the two systems

- Load and follow `visualize:visualize` before creating or updating the
  in-conversation visual. This skill owns source selection, study compression,
  and mastery safety; `visualize:visualize` owns the HTML fragment, interaction,
  accessibility, responsive layout, and content-reference contract.
- When an `obsidian-study-loop` vault is active, load and follow that skill too.
  Read `_study/state.json` at the start of the action and preserve its scope,
  evidence, timestamp, and persistence rules.
- Use `study-map` or `mind-map-obsidian` instead when the learner asks for a
  persistent, navigable vault map. Use the study loop's Markdown/Mermaid visual
  artifact lane when the learner explicitly asks to save a visual review in
  `_study/visuals/`.
- Never copy the Visualize plugin's UI rules into this skill. Treat its loaded
  instructions as the rendering authority.

## Resolve the chapter and source

1. Resolve the vault from an explicit path or from `STUDY-PROTOCOL.md`,
   `_study/state.json`, or `.obsidian/`. If no study vault is active, accept
   explicit local notes and operate read-only as a standalone visual study aid.
2. Resolve phrases such as "this chapter" or "the current chapter" from the
   active session and `## Unit progress`. If more than one chapter remains
   plausible, ask one short clarification before reading unrelated notes.
3. Find the existing source note or notes under the configured notes directory.
   In a study-loop vault, require the requested scope to have an assessment or
   a `## Notes written` record. Offer the normal quiz/write-notes path when the
   scope has not been established yet.
4. After the evidence gate below passes, read the complete in-scope source
   material. Inventory:
   - section and subsection headings;
   - terms and definitions;
   - explicit relationships, sequences, comparisons, and boundaries;
   - worked examples, limitations, exceptions, and exam tells;
   - verified links to other existing notes.
5. Keep a source ledger while composing: every visible node, edge, label,
   sequence, and distinction must resolve to a source note and heading. Omit
   unsupported connections and report missing linkage instead of inventing it.

## Protect evidence before visualizing

Run this gate after resolving candidate file paths but before reading details
that could answer a live question:

1. Scan the requested scope for unconsumed `## Quiz progress` blocks.
2. If an `active` or `paused` attempt contains an `asked` or `planned` question
   that overlaps the visual, stop and report the attempt and question exactly.
   Offer to resume the quiz, explicitly defer the affected question under the
   study-loop rules, or choose a non-overlapping chapter. Do not silently reveal
   the answer through a diagram.
3. Find unanswered in-scope `study-check` blocks. Offer a clean attempt before
   visualizing the tested concept. If the learner declines and proceeds, state
   that the visual is instruction and that a later answer is no longer clean,
   independent evidence; let `obsidian-study-loop` apply its evidence rules.
4. Never read, score, mutate, or summarize learner answers as a side effect of
   creating the visual. Never update assessment, confidence, review stage,
   note status, unit progress, or the active-session pointer.

## Build the chapter model

Choose one organizing question for the chapter, then use its natural section
grouping, normally three to seven sections. Do not manufacture sections to hit
a count. If the chapter needs more than seven, split it into numbered companion
surfaces rather than shrinking labels or creating an endless page.

Choose the smallest visual grammar that matches the source:

| Source relationship | Preferred visual |
|---|---|
| hierarchy, taxonomy, ownership | concept map or tree |
| ordered mechanism, procedure, attack, remediation | flow or sequence |
| close distinctions or repeated mappings | comparison or matrix |
| trust, access, dependency, containment | boundary or dependency map |
| change over time | timeline |
| real numeric observations | plot or chart |

Do not turn non-numeric prose into decorative charts. Preserve distinctions
that are easy to conflate, and keep limitations attached to the concept they
bound. When assessment history exists, open on the most fragile established
concept without displaying grades or inventing progress metrics.

## Compose a visual-first surface

- Create one visualization file per chapter surface. Keep a chapter in one file
  when it fits; use numbered companion surfaces when its real structure exceeds
  the section limit. Never combine the entire course into one dashboard.
- Make the first render useful without interaction: show the chapter's
  organizing structure and the current section.
- Use a compact section selector and one dominant visual canvas. Selecting a
  section should replace or update that canvas instead of scrolling to another
  block of prose.
- Keep node labels to short phrases. Put at most three concise supporting points
  in the selected-state detail, including a boundary, limitation, or exam tell
  only when the source supports it.
- Prefer progressive disclosure for examples and retrieval cues. Do not hide a
  concept's essential relationship behind a click.
- Label the surface `Visual study aid - not an assessment`.
- Allow only local, presentation-level interaction. Do not collect answers,
  score, persist completion, write browser storage, or imply mastery.
- Add a clearly labeled follow-up action through
  `window.openai.sendFollowUpMessage(...)` only when it materially helps the
  learner ask for teaching on the selected concept. Include the exact chapter,
  section, and source heading in that prompt.
- Avoid dashboard chrome, KPI cards, progress rings, decorative statistics,
  and repeated prose panels. The relationship diagram is the product.

## Generate and verify

1. Use `visualize:visualize` to write an HTML fragment in the thread-scoped
   writable visualization directory, never in the checked-out repository or
   the Obsidian vault.
2. Use the plugin's content reference in the same final response. Do not add a
   Markdown link to the fragment or describe implementation details.
3. Verify the primary section-selection interaction, keyboard access, concise
   labels, and source fidelity.
4. Verify light and dark themes and layouts at 736 px and 360 px. Use wide mode
   only when direct side-by-side comparison genuinely requires it.
5. Confirm that no source facts, sections, limitations, or distinctions were
   dropped during compression and that no future-scope material was added.

## Handle multi-chapter requests

When the learner asks to visualize every chapter:

1. Inventory only chapter notes that actually exist.
2. Report chapters blocked by missing notes, unestablished scopes, or active
   evidence collisions.
3. Generate a separate surface for each eligible chapter, starting with the
   current or most recently reviewed chapter.
4. Keep visual grammar stable where relationships repeat, but let each
   chapter's content determine its dominant diagram.

Do not create an all-course mega-surface. Cross-chapter navigation belongs to
`study-map`; focused comprehension belongs here.

## Persistence boundary

- Default to no vault writes. The HTML fragment is an in-conversation view of
  canonical notes.
- If the learner asks to save the visual in the vault, hand off to
  `obsidian-study-loop`'s current Markdown/Mermaid visual-review contract and
  validator. Never save or export the inline HTML into `_study/visuals/`.
- If the learner asks for a spatial Canvas or durable map stack, hand off to
  `mind-map-obsidian` or `study-map` and obey their integrity gates.
- A saved or inline visual remains a study aid. It never changes mastery until
  the learner answers a fresh question through the canonical quiz or reviewed
  `study-check` path.

## Completion check

- [ ] Chapter and source headings resolved from real files.
- [ ] No overlapping active quiz or unanswered study-check was leaked.
- [ ] Every visual relation is source-traceable.
- [ ] One chapter, one dominant canvas, and no long-scroll prose dump.
- [ ] Essential distinctions and limitations survived compression.
- [ ] Visualize interaction, accessibility, themes, and narrow layout verified.
- [ ] No vault, session, note, or mastery state changed during inline generation.
