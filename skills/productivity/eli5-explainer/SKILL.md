---
name: eli5-explainer
description: "Turn one hard topic into a beginner-friendly, picture-first HTML explainer saved as a single portable file: a large diagram per step, plain language, and an ordered walkthrough the reader can scroll or play. Inline CSS, JavaScript, and SVG only, with a restrictive CSP; a bundled dependency-free checker verifies structure, CSP, self-containment, the visible-word budget, and accessible names on inline SVGs. When the user supplies a screenshot, video, or page as a visual reference, inspect it first and follow its structure, spacing, palette, typography, and diagram language. Use when the user says ELI5, explain like I'm five, picture-first or visual explainer page, or wants a watchable walkthrough of a topic or study section. Do not use for graded work, persistent vault maps (study-map), in-conversation widgets (visualize-study-chapter), or slide decks."
# --- provenance ---
category: productivity
source: self-authored (this repository); feature list modeled on the public description of the ELI5 plugin, no plugin files copied
author: Sharquille Andrew
license: MIT
retrieved: 2026-09-27
---

# ELI5 explainer

One topic becomes one portable `.html` file a beginner can follow without a
wall of text. Pictures carry the mechanism; words label it.

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/eli5-explainer
```

## Scope

- One topic per page. If the request spans several, pick the one the user
  named first and list the rest as follow-ups.
- **Source-grounded.** When the topic comes from course material (a
  chapter-study-kit ledger, slides, notes), every claim on the page must be in
  that material. An everyday analogy is allowed only when it is labeled as an
  analogy and adds no new fact. Keep course terms exactly as the source spells them.
- Never write graded work. An explainer for a discussion or quiz topic teaches
  the concepts; it never drafts the answer, the post, or a personal story.
- An optional view, not a canonical source. It does not replace notes, maps, or
  a question bank, and it does not add another one. Link to the existing
  Practice file instead of building a quiz.

## Output location

Name the file `<topic-slug>-eli5.html`. A path the user names always wins.

- **Course topic** (the source lives in a course folder with `Week-XX_<dates>/`
  folders, such as `Monroe-University/<TERM>/<COURSE>/`): save to that course's
  `Week-XX_<dates>/Work/` for the week the source belongs to, so every subject
  keeps its explainers beside that week's review work. Take the week from the
  section's `state.json` `"week"` (chapter-study-kit) or from the week folder
  that holds the source; never infer it from `Chapter-NN`. If the week is
  unclear, ask. Add one line to that `Work/README.md` naming the file and what
  it covers. Never save into `Chapter-Kits/` or `Materials/`.
- **Any other topic:** the session scratchpad, and tell the user it is temporary.
- If a file with that name already exists, read it first and replace it only
  when it is an earlier version of the same explainer.

## Reference mode

When the user supplies a screenshot, video, or existing page as a reference,
read it in place before writing. Match its visible structure (sections, order),
spacing, palette, typography scale, and diagram language (line weight, shapes,
labels). Note which of those you matched and which you could not see. Do not
copy its text or trademarked marks.

## Page shape

| Part | Job | Limit |
| --- | --- | --- |
| Hero | The topic in one sentence plus one picture | 1 sentence |
| Steps | Ordered walkthrough; each step is one idea: big SVG, a short heading, at most two sentences | ≤ 40 words per step |
| Recap | One picture that puts every step back together | labels only |
| Footer | Source locators (deck and slide numbers, chapter) and the next place to study | 1–2 lines |

- Mark every step element `data-step="N"`, numbered 1..N in document order.
  Numbers encode the real sequence; do not number unordered facts.
- Give each recurring category (a code, a layer, a phase) one color and keep
  it on every step where that category appears.
- Visible words default to **900** or fewer. Pictures do the explaining.

## Build contract

- One file: `<!doctype html>`, `<html lang>`, charset and viewport meta, a
  specific `<title>` (a name, not a sentence).
- A CSP meta tag starting `default-src 'none'`. Allow only `'unsafe-inline'`
  style and script and `data:` images. No `http(s)://` or `//` sources in any
  `src`, `href`, `@import`, or `url()`. System font stacks only.
- Every inline `<svg>` has `role="img"` and an accessible name
  (`aria-label`, `aria-labelledby`, or a child `<title>`), or `aria-hidden="true"`
  when it is pure decoration.
- Complete at rest: every step is visible by scrolling with no script. Script
  only adds **watch mode**: Play/Pause, Back/Next, arrow keys, and a highlighted
  current step that advances on a timer.
- Light and dark palettes as tokens on `:root`, redefined under
  `prefers-color-scheme: dark` guarded by `:root:not([data-theme="light"])` and
  again under `:root[data-theme="dark"]`. Body sets an explicit background.
- Any animation or transition sits behind `prefers-reduced-motion`; watch mode
  scrolls without smoothing when reduced motion is on.
- Works at phone width: 16px side gutter, diagrams scale, no horizontal page scroll.

## Workflow

1. Resolve the topic and its sources. For a study kit, read the section
   `ledger.md` and Core notes; the Earned list is the content boundary.
2. Plan the steps: one idea each, in teaching order, with the picture you will
   draw. Check the plan against the sources before drawing. Recompute every
   number a picture shows (a mean, a median, a scaled bar) before building, and
   draw printed values to scale. Data invented only to show a pattern is a
   sketch or teaching example; say so in the footer.
3. Write a spec in the scratchpad, not in a course folder. A spec is a Python
   file that imports the SVG helpers (`svg`, `box`, `text`, `arrow`, `line`,
   `person`) from `eli5_page` and defines `PAGE`; copy the shape of
   [`references/example_spec.py`](references/example_spec.py). The shared shell
   supplies the CSP, both themes, the five category colors, and watch mode, so
   a spec holds only the pictures and words.
4. Build it. The builder renders the page, runs `eli5.py check` on it, and
   writes nothing if the check fails:

   ```sh
   python3 "$SKILL_DIR/scripts/eli5_page.py" "$SPEC" --root "<term folder>"   # course topic
   python3 "$SKILL_DIR/scripts/eli5_page.py" "$SPEC" --out "$FILE"            # any other topic
   ```

   `--root` resolves `<course>/Week-XX_*/Work/<slug>-eli5.html` from the spec's
   `course`, `week`, and `slug`, and adds the Work README line from `blurb`. It
   refuses a missing or ambiguous week folder and never replaces a file that is
   not an ELI5 page. Fix every reported error. For a hand-written page, run
   `python3 "$SKILL_DIR/scripts/eli5.py" check "$FILE"`; `--max-words N`
   changes the budget only when the user asks for a longer page.
5. Look at it once in a browser (one screenshot at desktop width), fix what that
   shows, and do not loop.
6. Optional publish as a claude.ai Artifact: convert, then publish the fragment
   with the Artifact tool under that host's page contract.

   ```sh
   python3 "$SKILL_DIR/scripts/eli5.py" artifact "$FILE" > "$SCRATCH/<topic-slug>-eli5.artifact.html"
   ```

   The converter keeps the title, styles, body, and scripts and drops the
   document wrapper and CSP meta, which the Artifact host replaces with its own.
7. Report the file path, the check result, what the screenshot showed, and any
   reference features you could not match.

## Done

- `eli5.py check` passes on the portable file.
- Every claim traces to the named sources; analogies are labeled.
- The page reads top to bottom with script off, and watch mode steps through it.
