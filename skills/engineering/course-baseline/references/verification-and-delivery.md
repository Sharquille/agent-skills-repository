# Verification and Delivery

Use this reference to turn "looks finished" into release evidence. Adapt commands
to the repository; preserve the gates and evidence categories.

## Contents

1. Verification policy
2. Gate sequence
3. Exercise and content tests
4. Runtime and simulator tests
5. Persistence and progression tests
6. Browser and visual tests
7. Accessibility and performance checks
8. Production build audit
9. Deployment verification
10. Git delivery
11. Closeout evidence

## 1. Verification policy

- Inspect the repository and its current test commands before proposing new ones.
- Capture the baseline before changing an existing course.
- Keep generated output, caches, and runtime downloads out of Git unless the
  deployment model requires them.
- Test the behavior the learner experiences, not only internal functions.
- Treat every expected solution, seeded defect, and grading rule as executable
  course code.
- Record exact pass, fail, skip, and warning counts.
- Do not weaken assertions, delete tests, or mark checks optional to obtain green.
- Name tests that were not run and the residual risk they leave.

## 2. Gate sequence

### Gate 0: source and contract

Verify:

- primary learner, outcomes, time budget, scope, story, and artifacts are explicit;
- each module maps to an outcome;
- each required tool has a real, browser-isolated, or field execution label;
- planted defects have a manifest and deterministic generator or fixture;
- deployment and persistence constraints are known.

### Gate 1: vertical slice

Prove one representative task end to end:

- content loads;
- input/tool starts;
- a correct answer passes;
- a wrong answer differs specifically;
- an error remains useful;
- a rejected anti-pattern is named;
- an attempt persists;
- the responsive workbench remains usable;
- a browser regression covers the journey.

Do not scale content until this gate passes.

### Gate 2: foundation pilot

Verify a small complete learning sequence with a real learner or an independent
evaluation pass. Record:

- where the learner paused or guessed;
- which hint level resolved the block;
- whether the artifact was usable;
- whether UI context distracted from the task;
- whether the estimated time was credible.

Revise the generating pattern before copying it to later modules.

### Gate 3: content complete

Verify all authored modules, solutions, links, artifacts, terminology, and
prerequisite edges. Confirm no placeholder or dead-end module is presented as
available.

### Gate 4: release candidate

Run the full unit, content, type/static, integration, browser, visual, build, and
preview gates. Run the bundled course audit in release mode.

### Gate 5: deployed

Verify the public URL from a clean browser context, including deep links, runtime
assets, persistence boundaries, and offline behavior when promised.

## 3. Exercise and content tests

For every exercise:

- execute the supplied solution against its exact seeds and checks;
- verify starter code is orienting but incomplete;
- verify expected outputs use stable ordering where order matters;
- verify unordered outputs do not fail because of row order;
- verify schema, type, row-count, invariant, required-pattern, and forbidden-
  pattern checks independently;
- verify null, empty, duplicate, malformed, repeated, and boundary cases;
- verify result diffs identify missing, unexpected, and changed values;
- verify raw errors do not leak protected solution content;
- verify rejected output explains the rule and downstream consequence;
- verify an honest attempt threshold cannot be reached with blank submissions.

For authored content:

- resolve every exercise/component ID;
- reject duplicate IDs;
- check internal links and artifact paths;
- lint banned synonym pairs when terminology consistency matters;
- check that every module exposes outcome, artifact, prerequisite, and exit task;
- scan for placeholders, unfinished examples, and contradictory tool names;
- verify time estimates against the actual work, not reading time alone.

## 4. Runtime and simulator tests

### Real browser or local runtime

Test:

- lazy loading and honest progress text;
- startup failure and retry;
- seeded input loading;
- correct and incorrect execution;
- worker and WebAssembly asset paths in production;
- large file and MIME requirements;
- offline cache behavior if promised;
- cleanup between exercises so state does not leak.

### Browser-isolated simulator

Unit-test the evaluator independently of the UI:

- correct command and arguments;
- correct command with missing argument;
- correct command with wrong argument;
- wrong command;
- unsupported flags;
- leading/trailing and repeated whitespace;
- quoted arguments where supported;
- pasted non-breaking hyphen and similar Unicode normalization;
- out-of-order command;
- repeated idempotent command;
- repeated non-idempotent command;
- current path/context changes;
- state after refresh;
- replay/reset behavior;
- progressive hint threshold.

Then cover at least one full lab in the browser. A simulator that accepts a
target substring or exact unparsed line is not releaseable.

### Field module

Verify the checklist names:

- exact external tool and supported version;
- setup prerequisites;
- task and expected evidence;
- privacy or secret-handling boundary;
- success check;
- common failure and recovery;
- acceptable proof format.

## 5. Persistence and progression tests

Test:

- first load with no data;
- save and immediate read;
- reload;
- browser restart when practical;
- schema migration;
- corrupted or partial record handling;
- reset of one lab versus reset of all progress;
- export and re-import if supported;
- progress blocked by failed upstream evidence;
- downstream unlock after a pass;
- failed and stale status behavior;
- attempt history ordering and restoration;
- runbook minimum-content validation;
- portfolio export names and file contents.

Progress must derive from evidence records. Do not maintain a disconnected
percentage that can disagree with module state.

## 6. Browser and visual tests

Run primary journeys on desktop and mobile projects. Include:

- course console renders with no console errors;
- next action routes correctly;
- blocked prerequisite routes to the exact requirement;
- workbench brief can collapse;
- focus mode increases tool width;
- editor/terminal accepts keyboard and paste;
- Run works by button and keyboard shortcut where advertised;
- correct solution passes;
- wrong result shows a diff;
- runtime error is visible;
- rejected anti-pattern is visible;
- hints progress without immediately exposing the answer;
- solution comparison unlocks at the intended threshold;
- attempt history restores a prior attempt;
- runbook saves and validates;
- persistence survives reload;
- mobile layout has no page-level horizontal overflow.

Capture screenshots for:

- console/map;
- module document;
- workbench default and focus modes;
- terminal/tool lab;
- each grading state;
- runbook and portfolio;
- narrow mobile and wide desktop.

Inspect screenshots. Pixel generation alone is not review.

## 7. Accessibility and performance checks

Verify:

- keyboard-only completion of the primary journey;
- visible focus and sensible focus order;
- labels for icon controls, terminal input, editor, and forms;
- semantic landmarks and heading order;
- status not conveyed by color alone;
- contrast on paper and console surfaces;
- reduced-motion mode;
- live updates announced without stealing focus;
- zoom to 200 percent without content loss;
- touch targets and text wrapping on mobile.

Measure:

- home screen load without large runtimes;
- lazy runtime load size and duration;
- production asset sizes;
- long-task or memory issues during repeated execution;
- service-worker cache size and update behavior;
- layout shift when status, hints, or results appear.

Set budgets from the actual audience and deployment target. A large runtime may
be justified, but it must not block the course console.

## 8. Production build audit

Before deployment:

1. install from the lockfile in a clean checkout when practical;
2. regenerate deterministic fixtures and verify no diff;
3. run content and terminology lint;
4. run unit and solution-contract tests;
5. run type/static checks;
6. run browser tests;
7. build production output;
8. run the release audit script;
9. serve the production output locally;
10. repeat the critical browser journey against the preview.

Inspect:

- ignored generated/runtime files;
- source maps and error leakage;
- environment variable requirements;
- secret-like files and staged secrets;
- SPA fallback requirements;
- worker, font, data, and WebAssembly paths;
- WebAssembly MIME type;
- maximum static asset size;
- service worker scope and update behavior;
- local-only progress disclosure.

Document exact install, dev, test, build, preview, and deploy steps in the target
project README.

## 9. Deployment verification

Choose the host from project constraints, not habit. A static local-first course
may use any host that supports its asset sizes, MIME types, HTTPS, and SPA
fallback. A backend course needs health, migration, secret, and rollback checks
appropriate to that service.

After deployment, use a clean browser context and verify:

- root URL;
- one deep module URL loaded directly;
- one workbench URL loaded directly;
- JavaScript, CSS, fonts, data, workers, and WebAssembly return successfully;
- no mixed content or CORS failures;
- runtime exercise execution;
- refresh persistence;
- service worker registration and update;
- offline reload if promised;
- mobile viewport;
- public metadata and repository link when present.

Record the public URL and deployment identifier. Do not call a repository push a
deployment unless the host actually updates from that push.

## 10. Git delivery

Before staging:

- inspect branch, status, diff, and remotes;
- identify user-owned or unrelated changes;
- confirm generated output and large runtimes are ignored intentionally;
- confirm the requested repository and branch;
- fetch or compare the remote branch when it already exists.

Stage an explicit allowlist. Then:

- review staged names and statistics;
- run staged whitespace checks;
- scan staged files for credentials, private keys, tokens, and local environment
  files;
- rerun the smallest release gate affected by any last change;
- commit with a message that describes the course-platform change;
- push normally without force;
- verify the remote branch SHA;
- verify repository description or deployment metadata only when requested.

Never discard unrelated work to make the tree clean. Never use a force push,
hard reset, or destructive clean as a release shortcut.

## 11. Closeout evidence

Report:

- learner and target outcome;
- implemented module range;
- real, simulated, and field tool boundaries;
- artifacts produced;
- exact test commands and pass/fail/skip counts;
- responsive and accessibility coverage;
- production build size and notable runtime assets;
- local preview URL;
- public URL and deployment ID, if deployed;
- branch, commit, and remote SHA, if pushed;
- excluded user files;
- remaining content, device, runtime, or deployment risks.
