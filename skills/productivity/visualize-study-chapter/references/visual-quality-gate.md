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
