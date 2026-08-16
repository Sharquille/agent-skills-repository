# Visual Explanation Quality Gate

Use this gate for every chapter endpoint build and every in-place redesign. It
exists because technically valid HTML can still be visually useless.

## Hard gates

Release fails when any of these are true:

- The primary scene is fundamentally a card grid, dashboard, or collection of
  prose boxes.
- The primary interaction only swaps text, opens another note panel, or changes
  decoration without changing the represented model.
- Removing paragraph text leaves no visible actor or object, relationship,
  direction, boundary, sequence, transformation, or consequence.
- One reusable geometry is relabeled across unrelated chapters. Reuse the shell
  and interaction infrastructure, not the chapter silhouette.
- An essential action is pointer-only, the useful first state requires motion,
  or the scene has no equivalent static explanation.
- A visible relation lacks a source-ledger entry, the page leaks active study
  evidence, requires a network connection, or changes mastery state.
- At 360 CSS pixels the learner must accept clipped labels, unreadable scaling,
  overlapping controls, or mandatory whole-scene horizontal panning.
- A desktop SVG is merely scaled down until its labels pass below 11 actual
  screen pixels. Computed CSS font size is not enough; transforms and the SVG
  viewBox affect what the learner can really read.
- The complete reference layer is expanded by default on a narrow screen and
  turns the chapter back into a long prose scroll even though the scene already
  carries the essential relationships.

## Minimum explanatory floor

One chapter surface must contain:

1. One organizing thesis and one concept-native signature scene.
2. At least four source-verified relationships encoded through position,
   connection, boundary, sequence, shape, pattern, or state rather than prose.
3. Three to five semantic actions such as trace, step, isolate, compare,
   reroute, alter, contain, or reset. The primary action changes at least two
   visual properties and makes its consequence visible before notes are read.
4. Short annotations anchored to the represented object or transition, plus a
   quiet linear reading layer for exact definitions, limitations, and sources.
5. A useful static first state, keyboard operation, visible focus, a concise
   accessible description, reduced-motion behavior, and deliberate 736px and
   360px compositions.

The selected state should normally form a closed explanatory trace: a cause or
starting condition, the affected object or boundary, and the visible
consequence. Highlighting an isolated path fragment or floating label does not
meet this floor.

For each state, apply the stricter four-part contract:

`input/starting condition → change or operation → concrete output/consequence → claim + limit`

Do not use a generic `result`, `effect`, `transform`, or icon-only claim row
when the source identifies the actual artifact or outcome. Name ciphertext,
digest, signature, alert, restored service, contained sample, rejected claim,
or another source-backed noun. If direction, ownership, or key use matters,
show arrowheads and place the owner/key label at the operation that consumes
it. A state-driven causal rail adjacent to the scene is acceptable as a
compact reading aid, but it must update with the selected state and must not
replace the primary relationship diagram with a prose card grid.

Apply a no-context read test: without using the chapter notes or prior study
knowledge, can a learner state what question the scene answers, follow the
input → operation → output path, and name the claim's boundary? If the answer
depends on already knowing the topic, the scene is polished decoration rather
than an intuitive teaching illustration. Every icon must earn its place by
identifying an object, action, owner, or consequence in that path.

At 360px, recompose the scene: change the viewBox, reflow the geometry, shorten
or relocate annotations, or remove nonessential decoration. Do not treat a
uniformly shrunken desktop scene as responsive design. Keep every visible SVG
label at least 11 actual screen pixels after scaling. The linear reference
layer may use a native `details` disclosure on narrow screens when the closed
state still contains exact definitions and the primary scene remains complete
without opening it.

When a mobile scene has a claim/limit footer, move the plate, icon, label, and
supporting line as one composition. A coordinate-only text move that detaches
copy from its visual anchor is a release blocker; leave visible breathing room
after the final process node before the footer begins.

Typography and layout are part of the explanation, not a finishing pass:
functional labels use a readable sans hierarchy, while monospace is reserved
for compact technical tokens, formulas, and metadata. Copy stays inside its
object or plate; claim and limit columns remain visibly separated; and no
decorative mark survives unless it communicates an object, operation, owner,
direction, boundary, or consequence. Check actual screen-space bounds for the
longest and densest labels, not only the SVG viewBox or a document-level
overflow result.

Ask one release question: **if the prose boxes disappeared, could the learner
still see what changed and why?** If not, redesign the scene.

## SVG and motion

- Prefer semantic inline SVG for systems, boundaries, paths, transformations,
  and state changes. Use native HTML controls; every pointer-selectable SVG
  object needs an equivalent keyboard-operable control.
- Keep visible labels as text, pair color with shape or line style, and provide
  an accessible name, description, and nearby static summary.
- Motion must be user-triggered and explain direction, causality, sequence,
  propagation, containment, or transformation. Do not add ambient loops,
  scanning lines, particles, parallax, flashing, or motion-only meaning.
- Reduced motion replaces travel with immediate state changes or ordered
  emphasis. Focus must not move when the scene changes.

## State-by-state release pass

- Inspect every selectable state, not only the initial screenshot. Include the
  longest label, densest state, destructive consequence, and recovery or
  verification state when present.
- At both 736px and 360px, check document overflow, control wrapping, label-to-
  object anchoring, label-to-line collisions, scene contrast, and actual
  screen-space text bounds. Repeat one dense state in light and dark themes.
- A selected action must visibly alter at least two properties and leave the
  system's unchanged context legible enough to explain what moved, stopped,
  crossed, transformed, or became contained.
- Review the densest and most easily conflated states for semantic correctness:
  verification must terminate at an independent owner or decision; distinct
  mechanisms such as RAT versus logic bomb and quarantine versus sandbox must
  have separate visible lanes; and a security-property claim must state what
  it does not establish (for example integrity is not secrecy, and a recorded
  ledger entry is not proof that the input was true).
- When pages are generator-backed, edit the generator first, regenerate every
  affected page and the index, then test the generated files. A hand-patched
  output that the next build will erase fails release.

## Optional sourced imagery

The skill adds no network dependency or automatic download. When the user has
already authorized web research and the environment permits it, a caller may
source an image only when it answers a specific learning question better than a
diagram. Download or embed an approved local copy so the surface stays offline.

Every sourced image needs documented origin, creator, license, retrieval date,
an educational caption, accurate alternative text, and a crop that preserves
the relevant evidence. Sanitize personal information, credentials, malicious
payloads, tracking data, and irrelevant identifiers. The chapter must retain a
complete vector or textual fallback.

Reject atmosphere-only stock imagery, code wallpaper, anonymous hacker
figures, locks, shields, random binary, and any picture whose removal changes
only mood rather than understanding.

## Rule exceptions

Low-level layout or style guidance may be broken when a source-accurate visual
relationship materially improves learning and the exception is recorded in the
build notes. Never break evidence protection, source traceability, privacy,
accessibility, offline integrity, or mastery boundaries. When rules conflict,
those safety and learning-integrity gates win.
