# Tactile Study Surface v2 — visual artifact template

The default visual system for `_study/visuals/` artifacts. Shared CSS and
compiled behaviors are combined with a declarative per-scope JSON manifest to
produce one self-contained offline HTML file.

## Files

- `chrome.css` — the token system and documented component primitives. It uses
  system fonts, provides light and dark modes, reduced-motion behavior, and
  print styles.
- `behaviors.ts` — the interaction source: theme toggle, rail scrollspy,
  retrieval reveal/hide/reset, ephemeral self-marks, and keyboard navigation.
- `behaviors.js` — the reviewed, compiled classic JavaScript shipped inline.
  Artifact generation reads this bundled file directly; it never downloads a
  compiler or invokes `npx`.
- `assemble.py` — validates a JSON manifest, rebuilds rich body fragments from
  an explicit HTML allowlist, escapes ordinary text, and writes the final HTML
  atomically.
- `example-content.json` — a generic worked manifest. Copy it when starting a
  new assessed scope.
- `example-content.py` — legacy pre-JSON example retained temporarily for
  repository history. Do not execute it or use it as an assembler input.

Run the assembler with Python's standard library only. The vault argument is
required so output and traceability remain confined to that vault:

```text
python3 assemble.py --vault <VAULT_PATH> example-content.json <VAULT_PATH>/_study/visuals/example.html
```

The input must have a `.json` extension and the output must have a `.html`
extension. The output must be directly inside the selected vault's real
`_study/visuals/` directory. Invalid JSON, unknown fields, unsafe markup,
unsafe or duplicate section IDs, symlink escapes, and nonexistent source notes
fail closed with a concise error. Existing symlinked output targets are refused.

## Manifest shape

The root object has exactly three fields:

- `meta` — `source`, `scope`, `code`, `scope_name`, `generated`, `title`,
  `accent`, `kicker`, `h1`, and `lede`.
- `sections` — an ordered non-empty array of objects with `id`, `nav`, `title`,
  `lede`, and `body_html`.
- `cues` — an array of `{ "question": ..., "reference": ... }` objects. Use an
  empty array when the source does not support honest retrieval cues.

All metadata, section labels, and cues are plain text and are HTML-escaped.
`source` must be a vault-local POSIX path that resolves to an existing regular
file inside the selected vault. `generated` must use a local ISO timestamp with
a numeric offset. `accent` accepts only a numeric
`oklch(L C H)` value, so it cannot become a CSS injection surface.

Section IDs must use lowercase words separated by single hyphens. They must be
unique and cannot use the template's reserved IDs: `main`, `top`, or
`retrieval`.

## Approved body primitives

`body_html` is the only rich field. The assembler parses it and emits a new
fragment instead of trusting the supplied string. Text nodes are escaped and
only these semantic elements are accepted:

```text
article code div em h3 li ol p span strong table tbody td th thead tr ul
```

Only `class` attributes are accepted, and only on the relevant primitive:

- `div`: `grid-2`, `grid-3`, `grid-4`, `flow`, `cols-3`, `cols-5`, `cols-6`,
  `duo`, `a`, `b`, `vs`, `table-wrap`, `contrast`, `chips`, `span-all`
- `article`: `card`, `span-all`
- `span`: `tag`, `warn`, `chip`, `vs-mark`

This vocabulary supports the surface's classification grids, cards and chips,
ordered flows, problem/response duos, pairwise contrasts, scrollable tables,
and boundary callouts. Unknown tags, classes, or attributes are errors. Body
IDs, URL-bearing attributes, event handlers, comments, declarations,
self-closing tags, scripts, styles, and SVG are rejected. When concept-native
SVG is essential, use the separately reviewed path in
`visual-review-standard.md`; do not place it in this manifest.

Follow the study narrative: orient → map or classify → contrast → respond or
apply. With non-empty cues, the assembler appends the retrieval deck and its
in-memory controls last. With empty cues, it emits no deck or JavaScript and
sets `script-src 'none'`.

## Interaction and release contract

- The deck's got-it/again marks are in-memory only. They reset on reload and
  are never stored, exported, scored, or written to mastery evidence.
- Released files contain no TypeScript, modules, imports, build tooling, remote
  resources, or runtime package downloads.
- When maintainers intentionally change `behaviors.ts`, compile and review
  `behaviors.js` in the repository using an already-installed compatible
  TypeScript compiler. Artifact authors do not rebuild it.
- After assembly, run `scripts/validate_study_vault.py <VAULT>` and complete
  the wide/narrow browser review described in `visual-review-standard.md`.
