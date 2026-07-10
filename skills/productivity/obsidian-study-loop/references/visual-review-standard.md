# Visual Review Artifact Standard

Use this reference when creating or redesigning HTML under
`_study/visuals/`. It turns the protocol's security boundary into a compact
design and review system. The protocol remains authoritative if the two ever
disagree.

## Design intent

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

## Required document posture

Every file includes:

- The exact visible label `Visual review artifact - not an assessment`.
- One logical `<h1>` and one `<main>` landmark.
- `lang`, UTF-8 charset, viewport, and `no-referrer` metadata.
- Non-empty `study-source`, `study-scope`, `study-generated`, and
  `study-visual-version` metadata. Contract version is `1`.
- A restrictive Content Security Policy with `default-src 'none'`,
  `connect-src 'none'`, `form-action 'none'`, and `base-uri 'none'`.
- A visible footer that repeats the scope, local source identifier, generation
  timestamp, and `Visual review only - not an assessment`.

Use a CSP shaped to the actual file. A no-script page can use:

```text
<meta http-equiv="Content-Security-Policy"
  content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; img-src data:; font-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
```

If classic inline JavaScript is essential, change only `script-src` to
`'unsafe-inline'`. Do not use module scripts, external files, hosts, or wildcard
sources.

## Accessibility and resilience

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

## Content structure

A strong page usually contains:

1. Posture banner, scope, and a one-sentence study purpose.
2. Signature diagram or relationship map.
3. Compact explanation or comparison blocks supporting that diagram.
4. Optional retrieval cues that ask the learner to explain, trace, compare, or
   name relationships without collecting an answer.
5. Traceability footer.

Retrieval cues use language such as `Trace the path`, `Explain the boundary`,
or `Compare these controls`. They do not use `submit`, `score`, `correct`,
`incorrect`, `pass`, `fail`, `mastered`, or answer-key framing.

## Forbidden surface

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
exceptions. Prefer inline SVG over encoded raster assets.

## Release review

1. Verify the artifact's scope exists in an assessment or notes-written record.
2. Run `scripts/validate_study_vault.py <VAULT_PATH>` and resolve every visual
   error.
3. Open the local file in a browser at wide and narrow widths.
4. Check reading order, clipping, deliberate overflow, SVG names, focus states,
   reduced motion, and print preview when provided.
5. Confirm the page attempts no network access.
6. Log the generated or regenerated artifact in the matching session's final
   `## Session log`.

Browser QA catches visual regressions; the validator catches deterministic
contract failures. Neither changes mastery evidence.
