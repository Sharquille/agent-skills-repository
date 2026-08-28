---
name: visualize-study-chapter
description: "Turn an existing study chapter or section into a compact, interactive, visual-first study surface using the Visualize plugin. Use when a learner asks to visualize a chapter, when a version 2 chapter reaches complete, to make dense notes easier to digest, replace long scrolling with concept maps, flows, comparisons, trust boundaries, or timelines, or create one visual surface per chapter from material already present in an obsidian-study-loop vault. Scope-locks every visual to real source notes, protects active applied-check evidence, and never changes mastery. Do not use to invent course content, grade the learner, make generic data charts, or create persistent Obsidian Canvas maps."
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
   active session and its version 2 `## Objective status` table (or legacy
   `## Unit progress`). If more than one chapter remains
   plausible, ask one short clarification before reading unrelated notes.
3. Find the existing source note or notes under the configured notes directory.
   In a version 2 study-loop vault, require every requested objective's Content
   gate to be `ready`. Legacy sessions may use an assessment or
   `## Notes written` record.
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
   Carry the exact note-and-heading provenance with each selectable state's
   input, operation, output, claim, and limit. When a control changes state,
   update that provenance with the visual trace; never leave a stale chapter-
   only source label beside a state-specific explanation.

## Protect evidence before visualizing

Run this gate after resolving candidate file paths but before reading details
that could answer a live question:

1. Scan the requested scope for unconsumed `## Quiz progress` blocks.
2. If an `active` or `paused` attempt contains an `asked` or `planned` question
   that overlaps the visual, stop and report the attempt and question exactly.
   Offer to resume the quiz, explicitly defer the affected question under the
   study-loop rules, or choose a non-overlapping chapter. Do not silently reveal
   the answer through a diagram.
3. In a version 2 session, an active or paused applied attempt is the only live
   evidence collision. For a legacy note, retain the unanswered in-scope
   `study-check` collision rule.
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

Read `references/visual-quality-gate.md` before composing or regenerating a
chapter surface. Its hard gates are release blockers, not aesthetic advice.
A primary scene made from repeated prose boxes or an interaction that only
swaps note panels is not a visualization and must be redesigned.

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
- Reuse navigation, accessibility, theme, and source-traceability
  infrastructure across chapters; do not reuse one generic scene geometry.
  Each chapter needs a concept-native silhouette and a primary interaction that
  visibly changes at least two model properties, such as path and boundary,
  position and connection, or state and consequence.
- Text serves as labels, annotations, and a linear fallback reading layer. If
  hiding paragraph text leaves no visible relationship, the surface is still
  decorated notes and fails the quality gate.
- Make every selectable state a closed explanatory trace: show a concrete input
  or starting condition, the visible change or operation, the concrete output
  or consequence, and a bounded claim plus limitation. Do not reuse generic
  labels such as `result`, `effect`, `transform`, or a floating claim taxonomy
  when the source names the actual artifact (for example ciphertext, digest,
  signature, alert, restored service, or contained host).
- When a mechanism has direction or ownership, draw the direction with
  arrowheads and label the owner or key at the point where it acts. When a
  claim is conditional, put the condition in the scene or its adjacent
  claim/limit rail rather than leaving it to the field notes.
- A compact causal rail directly adjacent to the primary scene is allowed when
  it is state-driven and uses short `input → change → output` labels plus
  `claim` and `limit` fields. It must update with the selected state and serve
  as a linear comprehension aid, not as a replacement for the relationship
  diagram or a stack of prose cards.
- Give each scene a visible purpose: the title or lead label should answer what
  the learner is meant to understand (for example, who owns a key, what
  crosses a boundary, or why a digest match is limited). Treat icons as
  semantic nouns only when their relationship and consequence are labeled;
  decorative icon rows do not count as explanation.
- Establish a small type system before placing geometry: use a readable sans
  for headings, object/action labels, and explanatory copy; reserve monospace
  for compact technical tokens, formulas, and metadata. Keep one clear visual
  hierarchy per scene and shorten copy before shrinking text below the
  readable-size gate.
- Reserve geometry safe zones before writing labels. Keep copy inside its
  object or plate, keep claim and limit columns separated, and leave deliberate
  breathing room after the final process node. A footer is one composition, not
  a second prose layer laid over the scene.
- Make visual stimulation causal rather than ornamental: every color, icon,
  line, arrowhead, boundary, and emphasis state must encode an object,
  operation, owner, direction, or consequence. Remove decoration that does not
  help the learner predict what changes next.
- Run a novice-only read test before release: temporarily ignore the notes,
  recall answer, and prior study context, then describe the selected state from
  the visual alone. If the input, operation, output, claim, or limitation
  cannot be recovered from the scene and its compact rail, redesign the scene
  instead of relying on the learner to infer the missing logic.
- Treat a dense mobile footer as one composition: move its plate, icon, label,
  and supporting line together in one explicit group or layout rule. Never
  move only the text coordinates after the card has been positioned. Leave a
  deliberate gap after the final process node before the claim/limit copy.
- On narrow screens, keep the relationship scene primary. A complete reference
  layer may be progressively disclosed with native HTML when the visible scene
  already carries the chapter model; do not force the learner through a long
  open prose ledger before the visual can be revisited.

## Generate and verify

1. At the chapter endpoint, write the HTML surface to the vault's study-site
   folder (`<vault>/Visuals/`) so the learner's link stays clickable across
   sessions — the surface is the durable output of the chapter, not a scratch
   file. Use the thread-scoped writable directory only for in-conversation
   previews when no vault is active.
2. Give the learner a clickable way to open the surface — this is the review
   or study entry point, and it is required at the chapter endpoint. In a
   vault, link to the persisted file (for example
   `<vault>/Visuals/1.2-security-controls.html`) or its plugin content
   reference; outside a vault, give a plain, copy-pasteable local path to the
   written fragment. Do not describe implementation details or add decorative
   prose around it.
3. Verify every section-selection state, not only the first: keyboard access,
   concise labels, source fidelity, cause-to-consequence continuity, and a
   visible change to at least two represented properties.
4. Verify light and dark themes and deliberate layouts at 736 px and 360 px.
   Measure actual rendered SVG text after viewBox scaling and keep it at least
   11 screen pixels; a uniformly shrunken desktop scene is not a mobile pass.
   Use wide mode only when direct side-by-side comparison genuinely requires
   it.
   At 360 px, recompose a dense causal diagram vertically or provide a
   state-driven adjacent causal rail with readable labels; do not rely on a
   uniformly shrunken desktop SVG.
5. Confirm that no source facts, sections, limitations, or distinctions were
   dropped during compression and that no future-scope material was added.
6. Keep the site navigable: when a vault `Visuals/` folder exists, refresh or
   create its `index.html` listing every built surface, so the folder works as
   a study site rather than a pile of files.
7. Apply the hard gates and acceptance checks in
   `references/visual-quality-gate.md`; regenerate rather than releasing a
   box-note surface that merely satisfies HTML validity.
8. If a source generator owns the surfaces, edit it first and regenerate all
   affected chapter files plus the index. Never release a hand-patched output
   that a later build will overwrite.

## Handle multi-chapter requests

When the learner asks to visualize every chapter:

1. Inventory only chapter notes that actually exist.
2. Report chapters blocked by missing notes, unestablished scopes, or active
   evidence collisions.
3. Generate a separate surface for each eligible chapter, starting with the
   current or most recently completed chapter.
4. Keep visual grammar stable where relationships repeat, but let each
   chapter's content determine its dominant diagram.

Do not create an all-course mega-surface. Cross-chapter navigation belongs to
`study-map`; focused comprehension belongs here.

## Chapter endpoint — build after completion, no request needed

The visual surface is the closing step of a completed chapter, not an optional
follow-up the learner must request. When every version 2 objective gate passes
and the active session reaches `complete`, build its surface automatically as
the final action of that chapter's cycle. A legacy session retains its older
review endpoint. Do not wait for the learner to say
"visualize it" as the last step.

- **Trigger:** the scope's completion record itself. If the learner asks for a
  visual at any point during the chapter, build it then too; the endpoint only
  guarantees the build happens even when they do not ask.
- **Gate first, always:** run "Protect evidence before visualizing" before the
  build. If a fresh active/paused applied attempt overlaps the scope, the
  endpoint reports the collision under the gate rules and defers the build —
  it never leaks an answer through a diagram. Unanswered `study-check` blocks
  remain a collision only in legacy notes.
- **Rebuild when the source changed:** regenerate a chapter's surface when its
  source note changed since the last surface; keep one surface per chapter and
  reuse the established visual grammar for that chapter.
- **Close with a link:** every endpoint build finishes by giving the learner a
  clickable way to open the surface to review or study (see Generate and
  verify, step 2). The link is the last thing the learner sees in that step.
- **Persist it:** the endpoint writes the surface into the vault's `Visuals/`
  folder (see Persistence boundary), so the link keeps working next session.
  If the vault has no `Visuals/` folder, create it on first build.

## Persistence boundary

- At the chapter endpoint, the surface is a durable artifact: write it to
  `<vault>/Visuals/<scope-slug>.html` and keep an `index.html` listing every
  built surface. This is the study site the endpoint's link points at, and it
  is the only allowed vault write this skill performs.
- Casual in-conversation visualizations that are not endpoint builds default
  to no vault writes: use the thread-scoped writable directory and treat the
  fragment as an in-conversation view of canonical notes.
- If the learner asks to save a visual review through the study loop's
  Markdown/Mermaid lane, hand off to `obsidian-study-loop`'s current
  visual-review contract and validator. Never save or export the inline HTML
  into `_study/visuals/` — that folder is the Markdown artifact lane.
- If the learner asks for a spatial Canvas or durable map stack, hand off to
  `mind-map-obsidian` or `study-map` and obey their integrity gates.
- A saved or inline visual remains a study aid. It never changes mastery until
  the learner answers a fresh question through the canonical applied-check
  path. Legacy sessions retain their preserved quiz or reviewed-check path.

## Completion check

- [ ] Chapter and source headings resolved from real files.
- [ ] No overlapping active applied attempt or legacy unanswered study-check was leaked.
- [ ] Every visual relation is source-traceable.
- [ ] One chapter, one dominant canvas, and no long-scroll prose dump.
- [ ] Essential distinctions and limitations survived compression.
- [ ] Visualize interaction, accessibility, themes, and narrow layout verified.
- [ ] Inline previews changed no vault, session, note, or mastery state.
- [ ] At the chapter endpoint, the surface was built automatically from the
      completion record — no "visualize it" request was required.
- [ ] The surface was persisted to `<vault>/Visuals/` (and `index.html`
      refreshed) so the link stays clickable across sessions.
- [ ] The final response gives the learner a clickable way to open the surface
      for review or study.
