# UI and Interaction Baseline

Use this reference to reproduce the feel of a calm, credible learning instrument:
dark operational chrome, readable document surfaces, real tools, compact
geometry, and concentration-first workspaces.

## Contents

1. Experience thesis
2. Required surfaces
3. Paper and console system
4. Baseline tokens
5. Typography
6. Layout and density
7. Course map
8. Module document
9. Workbench and terminal
10. Responsive behavior
11. Interaction and motion
12. Accessibility
13. Copy and feedback
14. Forbidden defaults
15. Visual audit

## 1. Experience thesis

The interface should feel like a professional tool used to learn professional
work. It is not a marketing site, a slide viewer, or a game layer wrapped around
content.

Use these principles:

- show the actual course as the first screen;
- let the subject determine the visual metaphors and data shown;
- separate orientation from concentration;
- make readable prose feel like a document;
- make execution feel like a real console or workbench;
- keep secondary context available but dismissible;
- use status color semantically, never as decoration;
- favor borders, spacing, and type over shadows and floating cards.

## 2. Required surfaces

Choose only the surfaces the course needs, but keep their responsibilities
separate.

### Console or course map

Show:

- the course or project name as a first-viewport signal;
- the dependency map or ordered route;
- module status and freshness;
- one next action;
- explicit scope boundaries when scope creep is a learner risk.

Do not repeat the full syllabus, analytics dashboard, and marketing explanation
on this screen.

### Module document

Show:

- title, outcome, duration, artifact, and prerequisite state;
- authored explanation and examples;
- the current stage in the learning sequence;
- a clear route into the lab;
- the operational handoff at the end.

Use a stable index or context rail on wide screens. On smaller screens, collapse
it into a compact header or drawer.

### Workbench

Show:

- stakeholder brief;
- editor, terminal, simulator, canvas, or real tool;
- execution output and checks;
- hints;
- attempt history;
- focus mode.

The tool and results receive most of the screen. Brief and history rails collapse
without losing state.

### Explorer

Use a data, schema, file, object, API, or system explorer when inspection is part
of the target skill. Keep it available from the workbench without forcing the
learner back through the course map.

### Portfolio

List passed artifacts with meaningful file paths, module provenance, and export
actions. Avoid certificate-first design.

### Runbook

Give operational notes a dedicated writing surface with structure, validation,
autosave or explicit saved state, and enough width for readable Markdown.

## 3. Paper and console system

Use two primary material roles:

1. **Console:** navigation, status, editors, terminals, logs, and execution.
2. **Paper:** long-form prose, briefs, decisions, rubrics, and documentation.

The contrast should be deliberate, not a theme toggle pasted onto every
component. Dark console chrome may frame a warm or neutral reading document, but
do not make the entire page beige or the entire product dark navy.

Adapt the palette to the domain while preserving:

- near-black with a visible hue for the app background;
- a distinct raised console surface;
- quiet but visible borders;
- a light reading surface with dark ink;
- one warm running/attention signal;
- muted verified and fault colors;
- a separate cool accent used sparingly for action and focus.

## 4. Baseline tokens

These LexLabs tokens are a fallback, not a universal brand:

| Role | Value | Use |
|---|---|---|
| console background | #0E1A1F | app chrome and deep workspace |
| console surface | #16303A | rails and raised execution panels |
| console border | #2C5C6B | dividers and inactive edges |
| paper | #EDE6D8 | reading document only |
| paper ink | #14252B | prose and strong labels |
| action accent | #3B766F | focused controls and links |
| running/stale | #E8A33D | active or freshness attention |
| verified | #4FA88B | passed evidence |
| fault | #C25450 | failed or rejected evidence |

Derive semantic tokens rather than scattering hex values: app background,
console surface, raised console surface, paper surface, text on console, text on
paper, muted text, subtle border, strong border, action, running, success, fault,
and focus ring.

Keep blue muted and subordinate. Do not use saturated blue for every button,
border, tab, progress mark, and heading. A course should not feel like a single
hue with different brightness values.

Use a radius scale no larger than 8px unless an existing design system requires
otherwise. Use shadows only when elevation communicates actual layering.

## 5. Typography

Use three roles:

- display sans for course and module identity;
- highly readable body face for sustained prose;
- monospaced face for commands, data, status, and code.

The LexLabs fallback is Bricolage Grotesque, Source Serif 4, and JetBrains Mono.
Use locally hosted or bundled fonts when offline behavior matters.

Rules:

- use one true page-level heading;
- keep panel headings compact;
- set prose to a comfortable measure, approximately 60-75 characters;
- use tabular numerals for metrics, time, progress, and results;
- keep letter spacing at zero unless the established brand explicitly differs;
- never scale font size directly with viewport width;
- prevent long commands, URLs, and artifact names from breaking containers.

## 6. Layout and density

Prefer full-width application bands and stable grids over floating page cards.
Cards are appropriate for repeated modules, discrete records, or modals, not for
wrapping every section.

Use:

- an 8px or 4px spacing system;
- stable toolbar and control dimensions;
- bounded reading width inside a full-height application;
- CSS grid tracks with minimums for editor/result panes;
- scroll containment so one pane does not drag the entire workspace;
- visible separators between responsibilities;
- compact status rows that support scanning.

Do not put cards inside cards. Do not use oversized hero type inside a compact
course console. Do not center every block.

## 7. Course map

Use a dependency graph only when the curriculum has real dependency semantics.
Otherwise use a concise ordered map.

For a graph:

- edges must communicate prerequisite direction;
- failed upstream work must visibly block downstream work;
- statuses need text or icons in addition to color;
- nodes need stable dimensions so labels do not shift the graph;
- long names must wrap without overlapping edges;
- keyboard users must reach every node;
- the mobile layout may become a vertical dependency list while preserving state.

Allow one restrained load sequence that resolves the graph in dependency order.
Respect reduced motion and avoid looping pulses except for a genuinely running
process.

## 8. Module document

Use a reading hierarchy:

1. compact metadata;
2. literal module title;
3. outcome and artifact;
4. explanation;
5. interactive task;
6. debrief and operational handoff.

Keep the prerequisite gate inside the document flow. A blocked state should
explain the exact upstream requirement and link directly to it.

Anti-patterns and warnings may use a fault-colored edge or hatched treatment, but
must remain readable and should not turn the entire page red.

## 9. Workbench and terminal

Use a top toolbar with familiar icons for back, show/hide brief, attempt history,
focus mode, reset, and run.

Give unfamiliar icon-only controls a tooltip and accessible label. Use text on
the primary Run command because its consequence matters.

Default wide-screen layout is brief rail, editor or tool, then results. Focus
mode removes the brief rail and gives the recovered width to the tool and
results. History should be a closable rail or drawer, not a permanent fourth
column. Notes and runbooks belong on another surface.

Terminal requirements:

- monospaced output and command history;
- stable prompt and current context;
- keyboard-first input;
- command output adjacent to the command;
- specific errors for wrong tool versus wrong argument;
- a visible "browser-isolated" label for a simulator;
- a replay control that resets lab state intentionally;
- no decorative emoji in commands or status;
- no arbitrary acceptance of a target substring.

Editor requirements:

- syntax support appropriate to the course;
- Run shortcut and visible Run button;
- loading state that names the runtime being prepared;
- reset starter action;
- read-only solution comparison mode;
- results table or diff that fits narrow screens without hiding columns silently.

## 10. Responsive behavior

Verify at least:

- narrow mobile around 375px;
- wide mobile or small tablet around 768px;
- desktop around 1280px;
- wide desktop around 1600px.

On mobile:

- stack the brief above the tool or place it in a drawer;
- keep Run reachable without horizontal scrolling;
- let result tables scroll within their region;
- avoid fixed sidebars;
- maintain a usable editor/terminal height with dynamic viewport units;
- keep tap targets at least 44px where practical;
- wrap status and artifact names;
- preserve a visible route back to the module.

Do not merely shrink a three-column desktop layout.

## 11. Interaction and motion

Use instant or short feedback for most interactions. Animate only transform and
opacity where possible. Keep interaction motion under 200ms.

Acceptable:

- a short panel reveal;
- graph resolution on first load;
- subtle focus/active transitions;
- progress indication for a real runtime load or running job.

Avoid:

- gradient movement;
- glowing active borders;
- ambient background blobs;
- bouncing completion states;
- perpetual pulses on static content;
- motion that changes layout dimensions.

## 12. Accessibility

Meet these minimums:

- semantic headings and landmarks;
- native controls before custom role-based controls;
- visible focus;
- keyboard access to every action;
- labels for editors, terminal inputs, forms, and icon buttons;
- contrast appropriate to both paper and console surfaces;
- status conveyed by text/icon as well as color;
- polite live regions for execution and saved states;
- focus restoration when drawers or dialogs close;
- reduced-motion behavior;
- no blocked paste in editors or command inputs.

## 13. Copy and feedback

Use concise operational language. Name:

- what the learner is doing;
- what passed or failed;
- which requirement differs;
- what action is available next.

Avoid in-app paragraphs that advertise features or explain the interface. Let
labels and behavior teach usage. Keep stakeholder briefs in the stakeholder's
voice and diagnostics in the tool's voice.

## 14. Forbidden defaults

Do not use:

- marketing hero pages as the course entry;
- split hero layouts with text beside a decorative illustration;
- generic blue/purple gradients;
- glassmorphism;
- blurred orbs or bokeh decoration;
- oversized rounded cards;
- nested cards;
- decorative numbered markers;
- XP, streak, confetti, or hollow achievement counters;
- permanent notes panels in active labs;
- aggressive bright blue across the entire theme;
- stock photography unrelated to the actual course work;
- visual terminals that cannot evaluate command behavior.

## 15. Visual audit

Capture desktop and mobile screenshots for every primary surface. Check:

- no overlap, clipping, or text outside controls;
- no unexpected horizontal page scroll;
- stable toolbar and node dimensions;
- readable prose measure and line height;
- sufficient contrast on both material systems;
- focus mode actually increases working area;
- collapsed rails do not leave dead space;
- result diffs and tables remain understandable;
- empty, loading, error, rejected, passed, blocked, and stale states are polished;
- the subject or project is visible in the first viewport;
- the next section or route is discoverable without a marketing scroll.

Use screenshots as evidence of rendering only. Pair them with interaction tests
and console-error capture.
