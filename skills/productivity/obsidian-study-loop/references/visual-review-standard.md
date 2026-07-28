# Visual Review Artifact Standard

Use this reference when creating or redesigning Markdown visual reviews under
`_study/visuals/`. The active artifact format is Markdown with Mermaid so the
same file remains reachable and renderable in Obsidian on desktop and iPadOS.
The protocol remains authoritative if the two ever disagree.

## Active Markdown and Mermaid contract

A generated artifact is
`<VAULT>/_study/visuals/<YYYY-MM-DD>-<scope-slug>.md`. Never generate a new
`.html` artifact. Existing `.html` artifacts remain supported by the separate
legacy contract below.

Every Markdown artifact has YAML frontmatter with these four fields:

```yaml
---
study-source: Notes/Topic.md
study-scope: 2.3 Topic
study-generated: 2026-07-09T12:30:00-0400
study-visual-version: 2
---
```

Each `study-*` value is a bare scalar on one line. Quoted and multiline values
are forbidden. `study-source` is a vault-local POSIX path to an existing regular
file inside the vault, never a URL. Extension dispatch happens before contract
selection: `.md` requires version `2`; legacy `.html` requires version `1`.

The body must:

- Show the exact label `Visual review artifact - not an assessment`.
- Contain one logical `#` H1, with `##` headings for body sections.
- Use Markdown, Mermaid, compact tables, and Obsidian callouts to explain only
  the assessed or written scope.
- Avoid remote images and external link dependencies. Markdown link and image
  destinations and raw HTML URL attributes may use vault-relative paths or
  fragments only. `http:`, `https:`, `//`, and all other external schemes are
  errors.
- Contain no answer collection, scoring, grading, persistence, or mastery
  writes.

Scope locking is a human gate. The validator checks that `study-source` exists
as a vault-local regular file; it does not cross-check `study-scope` against
session assessments or notes-written records.

Obsidian Canvas is a manual option for large spatial maps, but generated visual
reviews never create `.canvas` files and the validator ignores them.

### Mermaid structural checks

The validator performs deterministic structural checks, not Mermaid parsing.
Fences must be balanced and well formed. Unterminated fences, empty `mermaid`
blocks, and malformed or nested fence boundaries are errors.

The first non-empty line in each Mermaid block must begin with a recognized
diagram declaration. The allowlist is: `flowchart`, `graph`,
`sequenceDiagram`, `classDiagram`, `stateDiagram`, `stateDiagram-v2`,
`erDiagram`, `journey`, `gantt`, `pie`, `mindmap`, `timeline`,
`quadrantChart`, `gitGraph`, `sankey-beta`, `xychart-beta`, and `block-beta`.
An unknown declaration is an error because Obsidian renders it as an error box.

A quoted Mermaid label must not begin with a list marker: `1.`, `1)`, `- `, or
`* `. That lexical pattern can silently fail in Obsidian.

### Retrieval prompts

Use foldable Obsidian callouts:

```markdown
> [!QUESTION]- Which key encrypts for confidentiality?
> The recipient's public key. Only their private key decrypts.
```

The hidden response is a study aid, not evidence. To turn a prompt into mastery
evidence, ask it again through the normal chat quiz or reviewed study-check
path.

### Release review

1. Verify manually that the artifact scope has already been assessed or written.
2. Run `scripts/validate_study_vault.py <VAULT_PATH>` and resolve every visual
   error.
3. Open the Markdown file in Obsidian on a target device.
4. Confirm every Mermaid diagram renders, callouts fold, hierarchy is readable,
   and local links resolve.
5. Log the generated or regenerated artifact under the matching session's
   `## Session log`.

Full rendering fidelity is human/Obsidian QA. The validator's deterministic
checks do not prove rendering fidelity, scope coverage, or mastery.

## Legacy HTML contract

The contract below is retained only so existing `.html` artifacts continue to
validate cleanly. It is no longer the active visual system and must not be used
to generate new artifacts.

### Design intent

A visual review artifact is a study diagram, not a dashboard or quiz shell. Its
single job is to make relationships inside one already assessed or written
scope easier to see and recall.

Ground the design in the subject:

- Choose a visual grammar that matches the material: control plane, attack
  path, taxonomy, process flow, trust boundary, timeline, or comparison grid.
- Make one concept-native diagram the signature element. Keep surrounding
  cards, labels, and decoration quiet enough that the diagram remains primary.
- Use a compact palette of four to six named CSS custom properties. Color must
  encode stable meaning, not merely decorate.
- Use local system font stacks only. Give display, body, and utility text clear
  roles through size, weight, width, or case rather than remote fonts.
- Avoid generic KPI tiles, decorative charts, ornamental gradients, fake
  terminal chrome, or arbitrary numbered steps unless the source material
  genuinely contains metrics, commands, or sequence.

### Legacy tactile study surface (v2)

The former default experience is the tactile study surface: a precise, keyboard-
friendly technical reading interface defined by flow and information
architecture, not decoration. Build it from the bundled template in
`tactile-study-surface/` (chrome, compiled behaviors, assembler, worked
example — see its `SPEC.md`), so every artifact shares byte-identical chrome
and only the declarative per-scope JSON manifest changes.

#### Narrative flow

Arrange supported content in this order:

1. **Orient** - scope, thesis, and the question that organizes the page.
2. **Map or classify** - the dominant relationship, taxonomy, boundary, or
   decision structure.
3. **Contrast** - close pairs, matrices, exceptions, and tell lines.
4. **Respond or apply** - process, remediation, ownership, or a worked decision.
5. **Retrieve** - native disclosures that withhold the reference until opened.

Do not manufacture a stage when the note has no supporting content. The source
scope controls the page, never the template.

#### Visual grammar

- Tactile technical surface: oklch tokens, system font stacks only, 1px
  borders with hard asymmetric shadows, small radii, a subtle graph-paper
  texture, compact monospace utility labels, and one per-scope accent hue
  with coral reserved for traps and tells.
- Stable frame from the template: sticky command bar (scope code, keyboard
  hints, theme toggle), scrollspy index rail that becomes a wrapped
  horizontal index on narrow screens, one strong thesis, numbered section
  panels, an optional retrieval deck last, traceability footer.
- One thesis and one signature visual dominate. Supporting content uses the
  template primitives — cards with tags and chips, flows, duo splits, vs
  pairs, tables in scroll wrappers, and contrast callouts.
- Light is the reading default; dark follows `prefers-color-scheme` or the
  in-memory toggle. Design mobile-first at 320 CSS pixels; the frame
  collapses to a single column below 900 pixels.

#### Mind-map routing

Use a mind map for real hierarchy, branching, taxonomy, ownership, or
one-to-many relationships. Use a comparison for two-sided distinctions, a
matrix for repeated exact mappings, and a flow or timeline for ordered stages.
Every node and edge must be traceable to the source note. A mind map may reveal
detail on selection, but must not collect answers or imply scoring.

#### Maintainer interaction boundary

Normal study-time generation uses the bundled reviewed `behaviors.js` and must
not invoke package managers, install dependencies, or download a compiler.
`behaviors.ts` is maintainer source only. Rebuild it only during repository
maintenance with an already-installed pinned compiler, then inspect and test
the compiled diff. The released artifact remains one offline HTML file: no
TypeScript runtime, JSX, Tailwind runtime, package import, module script, source
map, or external dependency. Static pages should remain script-free.

#### Content-preservation gate

Before an in-place redesign, inventory headings, factual paragraphs, examples,
comparisons, limitations, scope boundaries, and retrieval references. After the
redesign, compare the inventory. Missing, rewritten, broadened, or silently
collapsed subject matter blocks release even when the page looks better.

### Required document posture

Every file includes:

- The exact visible label `Visual review artifact - not an assessment`.
- One logical `<h1>` and one `<main>` landmark.
- `lang`, UTF-8 charset, viewport, and `no-referrer` metadata.
- Non-empty `study-source`, `study-scope`, `study-generated`, and
  `study-visual-version` metadata. `study-source` is a vault-local POSIX path
  to an existing regular file inside the vault. Contract version is `1`.
- A restrictive Content Security Policy with `default-src 'none'`,
  `connect-src 'none'`, `form-action 'none'`, and `base-uri 'none'`.
- A visible footer that repeats the scope, local source identifier, generation
  timestamp, and `Visual review artifact - not an assessment`.

Use a CSP shaped to the actual file. A no-script page can use:

```text
<meta http-equiv="Content-Security-Policy"
  content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; img-src data:; font-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
```

If classic inline JavaScript is essential, change only `script-src` to
`'unsafe-inline'`. Do not use module scripts, external files, hosts, or wildcard
sources.

### Accessibility and resilience

- Use semantic HTML before ARIA. Native `<details>` and `<summary>` are the
  default disclosure pattern.
- Give informative SVGs an `aria-label` or `aria-labelledby`. Mark decorative
  SVGs `aria-hidden="true"`.
- Use real links and `button type="button"` for actions. Never use forms or
  data-entry controls.
- Provide a visible `:focus-visible` treatment whenever the document contains
  links, buttons, details, or summaries.
- Keep body text contrast at least 4.5:1 and large text or graphical UI at
  least 3:1.
- Reflow at 320 CSS pixels without lost information. Wrap intentionally wide
  tables or code in a labelled overflow container instead of shrinking text.
- If motion or transitions exist, include a complete
  `prefers-reduced-motion: reduce` override. Motion must clarify state or
  sequence; ambient motion is usually unnecessary.
- Add a print stylesheet when the page benefits from paper review. Print is a
  quality enhancement, not a validator gate.

### Content structure

A strong page usually contains:

1. Posture banner, scope, and a one-sentence study purpose.
2. Signature diagram or relationship map.
3. Compact explanation or comparison blocks supporting that diagram.
4. Optional retrieval cues that ask the learner to explain, trace, compare, or
   name relationships without collecting an answer.
5. Traceability footer.

Retrieval cues use language such as `Trace the path`, `Explain the boundary`,
or `Compare these controls`. They do not use `submit`, `score`, `correct`,
`incorrect`, `pass`, `fail`, `mastered`, or answer-key framing. The deck's
reveal controls and got-it/again self-marks are permitted precisely because
they are ephemeral: in-memory only, reset on reload, never collected, stored,
exported, scored, or written to mastery evidence — adding persistence to them
breaches this contract.

### Forbidden surface

Do not add:

- Remote or relative resources, network calls, telemetry, accounts, service
  workers, or cross-file dependencies.
- Forms, inputs, textareas, selects, answer collection, grading, scoring,
  completion tracking, or persistence.
- Browser storage, cookies, clipboard writes, device APIs, dynamic imports,
  `eval`, function constructors, or inline event-handler attributes.
- Iframes, objects, embeds, external scripts, external stylesheets, web fonts,
  or links that leave the document.

Fragment links and inline `data:image/` resources are the only URL-bearing
exceptions. The JSON tactile assembler deliberately rejects SVG. If a
concept-native diagram truly needs inline SVG, author it through a separately
reviewed offline artifact, give it the accessibility treatment below, and run
the same validator and browser checks; never smuggle SVG through `body_html`.

### Release review

1. Verify the artifact's scope exists in an assessment or notes-written record.
2. For an in-place redesign, complete the content-preservation inventory and
   confirm that all source matter remains represented.
3. Run `scripts/validate_study_vault.py <VAULT_PATH>` and resolve every visual
   error.
4. Open the local file in a browser at wide and narrow widths.
5. Check reading order, clipping, deliberate overflow, SVG names, focus states,
   reduced motion, and print preview when provided.
6. Confirm the page attempts no network access.
7. Log the generated or regenerated artifact in the matching session's final
   `## Session log`.

Browser QA catches visual regressions; the validator catches deterministic
contract failures. Neither changes mastery evidence.
