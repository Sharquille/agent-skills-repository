# Tactile Study Surface v2 — visual artifact template

The default visual system for `_study/visuals/` artifacts. One shared chrome
(CSS + compiled behaviors) plus per-scope content, assembled into a single
self-contained offline HTML file that satisfies the visual-artifact contract.

Files in this directory:

- `chrome.css` — the full token system and components. oklch colors, system
  font stacks only, hard asymmetric shadows, graph-paper texture, light
  default with dark via `prefers-color-scheme` and a `data-theme` override,
  `prefers-reduced-motion` and print styles included.
- `behaviors.ts` — the interaction source of truth: theme toggle, index-rail
  scrollspy (IntersectionObserver), retrieval-deck reveal/hide/reset,
  ephemeral self-marks with a tally, and j/k/o/g/a/t keyboard driving. All
  state is in-memory and dies with the tab; no storage, network, eval, or
  inline handlers.
- `behaviors.js` — the compiled classic-JS block that ships inline. Rebuild
  after any `.ts` change (TypeScript 7 native compiler, GA 2026-07-08):

  ```text
  npx -y -p typescript@7 tsc behaviors.ts --strict --target es2019 --lib dom,es2019 --noEmitOnError
  ```

- `assemble.py` — builds a final artifact from this chrome plus a content
  module: `assemble.py <content-module.py> <output.html>`. Guarantees every
  artifact carries byte-identical chrome, the correct CSP
  (`script-src 'unsafe-inline'`, everything else denied), the four `study-*`
  metas, the posture banner, and the traceability footer.
- `example-content.py` — a complete worked content module (the 2.3 Malware
  scope). Copy it as the starting point for a new scope.

## Content module shape

A content module defines three values:

- `META` — `source`, `scope`, `code`, `scope_name`, `generated`, `title`,
  `accent` (one oklch value; give each scope a stable identity hue), `kicker`,
  `h1` (the thesis), `lede`.
- `SECTIONS` — ordered list of dicts: `id`, `nav` (rail label), `title`,
  `lede`, `body` (inner HTML built from the primitives below). Follow the
  narrative flow: orient → map or classify → contrast → respond or apply;
  the assembler appends the retrieval deck last.
- `CUES` — list of `(question, reference)` pairs for the retrieval deck.

## Component primitives (use these, don't invent new chrome)

- `.grid-2/3/4` + `.card` (+ `.tag`, `.tag.warn`, `.chips`/`.chip`,
  `.span-all`) — classification boards, actor/technique/family cards.
- `.flow` (+ `.cols-3/5/6`) — numbered stages, kill chains, remediation
  ladders, control-type timelines.
- `.duo` — exposure/fix or problem/response split pairs.
- `.vs` — high-confusion pair contrasts with a VS mark.
- `.table-wrap > table` — matrices and coordinate grids (deliberate
  horizontal scroll on narrow screens).
- `.contrast` — coral-edged callout for traps, tells, and boundary notes.

## Contract notes

- The deck's got-it/again marks are deliberately ephemeral: in-memory only,
  reset on reload, never stored, exported, scored, or written to mastery
  evidence. Keep it that way — persistence would breach the artifact
  contract.
- The released file must contain no TypeScript, modules, imports, or build
  tooling — only the compiled classic inline block.
- After assembling, run `scripts/validate_study_vault.py <VAULT>` and do the
  wide/narrow browser check per the release review in
  `visual-review-standard.md`.
